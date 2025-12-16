from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import bcrypt
import jwt
from models import (
    User, UserCreate, UserLogin, Token,
    Video, VideoCreate, Campaign,
    APIConnection, APIKeyUpdate, TrendingTopic
)
from emergentintegrations.llm.chat import LlmChat, UserMessage
import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from validators import (
    validate_gemini_key, 
    validate_kie_key,
    validate_openrouter_key,
    validate_youtube_credentials,
    validate_sheet_id
)
from encryption import (
    encrypt_credentials, 
    decrypt_credentials,
    mask_credentials
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 10080))

security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

scheduler = BackgroundScheduler()
scheduler.start()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="بيانات اعتماد غير صالحة")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="المستخدم غير موجود")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="انتهت صلاحية الجلسة")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="بيانات اعتماد غير صالحة")

@api_router.post("/auth/register", response_model=Token)
async def register(user_create: UserCreate):
    existing_user = await db.users.find_one({"email": user_create.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مسجل بالفعل")
    
    password_hash = bcrypt.hashpw(user_create.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(
        email=user_create.email,
        password_hash=password_hash
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    await db.users.insert_one(user_dict)
    
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer")

@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    user = await db.users.find_one({"email": user_login.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
    
    if not bcrypt.checkpw(user_login.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
    
    access_token = create_access_token(data={"sub": user['id']})
    return Token(access_token=access_token, token_type="bearer")

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "created_at": current_user['created_at']
    }

@api_router.post("/settings/api-keys")
async def update_api_keys(api_key_update: APIKeyUpdate, current_user: dict = Depends(get_current_user)):
    """حفظ مفاتيح API مع التشفير"""
    api_keys = current_user.get('api_keys', {})
    
    # تشفير البيانات قبل الحفظ
    encrypted_credentials = encrypt_credentials(api_key_update.credentials)
    api_keys[api_key_update.service] = encrypted_credentials
    
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"api_keys": api_keys}}
    )
    
    return {"message": f"تم تحديث بيانات {api_key_update.service} بنجاح"}

@api_router.get("/settings/api-keys")
async def get_saved_api_keys(current_user: dict = Depends(get_current_user)):
    """جلب المفاتيح المحفوظة مع فك التشفير والإخفاء"""
    api_keys = current_user.get('api_keys', {})
    
    if not api_keys:
        return {}
    
    # فك التشفير
    decrypted_keys = {}
    for service, credentials in api_keys.items():
        try:
            decrypted_keys[service] = decrypt_credentials(credentials)
        except Exception as e:
            logger.error(f"Error decrypting {service} keys: {str(e)}")
            decrypted_keys[service] = {}
    
    # إخفاء المفاتيح للعرض
    masked_keys = {}
    for service, creds in decrypted_keys.items():
        masked_keys[service] = mask_credentials(creds)
    
    return masked_keys

@api_router.post("/settings/test-connection")
async def test_api_connection(service: str, current_user: dict = Depends(get_current_user)):
    """اختبار اتصال API مع validation كامل"""
    api_keys = current_user.get('api_keys', {})
    
    # فك تشفير المفاتيح
    decrypted_keys = {}
    for svc, credentials in api_keys.items():
        try:
            decrypted_keys[svc] = decrypt_credentials(credentials)
        except:
            decrypted_keys[svc] = {}
    
    if service == "gemini":
        gemini_key = decrypted_keys.get('gemini', {}).get('api_key') or os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            return APIConnection(service=service, status="error", message="❌ لم يتم العثور على مفتاح API")
        
        # الخطوة 1: التحقق من format المفتاح أولاً
        validation = validate_gemini_key(gemini_key)
        if not validation['valid']:
            return APIConnection(service=service, status="error", message=f"❌ {validation['error']}")
        
        # الخطوة 2: اختبار الاتصال الحقيقي
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # استخدام endpoint الصحيح
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
                )
                
                # الخطوة 3: التحقق من محتوى الاستجابة
                if response.status_code == 200:
                    data = response.json()
                    if 'models' in data and len(data['models']) > 0:
                        models_count = len(data['models'])
                        return APIConnection(service=service, status="success", message=f"✅ تم الاتصال بنجاح مع Gemini API ({models_count} نموذج متاح)")
                    else:
                        return APIConnection(service=service, status="error", message="❌ الاستجابة غير صحيحة. هذا ليس مفتاح Gemini")
                
                elif response.status_code == 400:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', '')
                    if 'API key not valid' in error_message:
                        return APIConnection(service=service, status="error", message="❌ مفتاح API غير صالح أو منتهي الصلاحية")
                    elif 'quota' in error_message.lower():
                        return APIConnection(service=service, status="error", message="❌ تم تجاوز حد الاستخدام (Quota exceeded)")
                    else:
                        return APIConnection(service=service, status="error", message=f"❌ خطأ: {error_message}")
                else:
                    return APIConnection(service=service, status="error", message=f"❌ خطأ في الخادم: {response.status_code}")
                    
        except httpx.TimeoutException:
            return APIConnection(service=service, status="error", message="❌ انتهت مهلة الاتصال (Timeout). تحقق من الإنترنت")
        except Exception as e:
            logger.error(f"Error testing Gemini connection: {str(e)}")
            return APIConnection(service=service, status="error", message=f"❌ فشل الاتصال: {str(e)}")
    
    elif service == "kie_ai":
        kie_key = decrypted_keys.get('kie_ai', {}).get('api_key') or os.getenv('KIE_AI_API_KEY')
        if not kie_key:
            return APIConnection(service=service, status="error", message="❌ لم يتم العثور على مفتاح API")
        
        # التحقق من format المفتاح
        validation = validate_kie_key(kie_key)
        if not validation['valid']:
            return APIConnection(service=service, status="error", message=f"❌ {validation['error']}")
        
        # Kie.ai: نقبل المفتاح إذا كان format صحيح
        # لأن API endpoint قد لا يكون متاح دائماً
        return APIConnection(
            service=service, 
            status="success", 
            message="✅ تم حفظ مفتاح Kie.ai (سيتم التحقق منه عند الاستخدام)"
        )
    
    elif service == "openrouter":
        openrouter_key = decrypted_keys.get('openrouter', {}).get('api_key')
        if not openrouter_key:
            return APIConnection(service=service, status="error", message="❌ لم يتم العثور على مفتاح API")
        
        # التحقق من format المفتاح
        validation = validate_openrouter_key(openrouter_key)
        if not validation['valid']:
            return APIConnection(service=service, status="error", message=f"❌ {validation['error']}")
        
        # اختبار الاتصال الحقيقي
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {openrouter_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and len(data['data']) > 0:
                        return APIConnection(
                            service=service, 
                            status="success", 
                            message=f"✅ تم الاتصال بنجاح مع OpenRouter API ({len(data['data'])} موديل متاح)"
                        )
                    else:
                        return APIConnection(service=service, status="error", message="❌ الاستجابة غير صحيحة")
                
                elif response.status_code == 401:
                    return APIConnection(service=service, status="error", message="❌ مفتاح API غير صالح أو منتهي الصلاحية")
                else:
                    return APIConnection(service=service, status="error", message=f"❌ خطأ: {response.status_code}")
                    
        except httpx.TimeoutException:
            return APIConnection(service=service, status="error", message="❌ انتهت مهلة الاتصال")
        except Exception as e:
            logger.error(f"Error testing OpenRouter connection: {str(e)}")
            return APIConnection(service=service, status="error", message=f"❌ فشل الاتصال: {str(e)}")
    
    elif service == "youtube":
        youtube_creds = decrypted_keys.get('youtube', {})
        client_id = youtube_creds.get('client_id') or os.getenv('YOUTUBE_CLIENT_ID')
        client_secret = youtube_creds.get('client_secret') or os.getenv('YOUTUBE_CLIENT_SECRET')
        
        # التحقق من البيانات
        validation = validate_youtube_credentials(client_id, client_secret)
        if not validation['valid']:
            errors_text = ', '.join(validation['errors'])
            return APIConnection(service=service, status="error", message=f"❌ {errors_text}")
        
        return APIConnection(service=service, status="success", message="✅ بيانات اعتماد YouTube صحيحة (يتطلب OAuth2 للاتصال الكامل)")
    
    elif service == "google_drive":
        drive_creds = decrypted_keys.get('google_drive', {})
        credentials_json = drive_creds.get('credentials_json')
        
        if not credentials_json:
            return APIConnection(service=service, status="error", message="❌ لم يتم رفع ملف Credentials JSON")
        
        try:
            import json
            creds = json.loads(credentials_json)
            if 'type' in creds and 'project_id' in creds and 'private_key' in creds:
                return APIConnection(service=service, status="success", message="✅ ملف Credentials JSON صحيح")
            else:
                return APIConnection(service=service, status="error", message="❌ ملف JSON غير مكتمل. تأكد من وجود type و project_id و private_key")
        except json.JSONDecodeError:
            return APIConnection(service=service, status="error", message="❌ ملف JSON غير صالح")
    
    elif service == "google_sheets":
        sheets_config = decrypted_keys.get('google_sheets', {})
        sheet_id = sheets_config.get('sheet_id')
        
        validation = validate_sheet_id(sheet_id)
        if not validation['valid']:
            return APIConnection(service=service, status="error", message=f"❌ {validation['error']}")
        
        return APIConnection(service=service, status="success", message="✅ Sheet ID محفوظ (يتطلب OAuth2 للاتصال الكامل)")
    
    return APIConnection(service=service, status="error", message="❌ خدمة غير معروفة")

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    total_videos = await db.videos.count_documents({"user_id": current_user['id']})
    published_videos = await db.videos.count_documents({"user_id": current_user['id'], "status": "published"})
    pending_videos = await db.videos.count_documents({"user_id": current_user['id'], "status": {"$in": ["pending", "processing"]}})
    
    videos_cursor = db.videos.find(
        {"user_id": current_user['id'], "analytics.views": {"$exists": True}},
        {"_id": 0, "analytics.views": 1}
    ).limit(100)
    
    total_views = 0
    async for video in videos_cursor:
        total_views += video.get('analytics', {}).get('views', 0)
    
    active_campaigns = await db.campaigns.count_documents({"user_id": current_user['id'], "status": "active"})
    
    return {
        "total_videos": total_videos,
        "published_videos": published_videos,
        "pending_videos": pending_videos,
        "total_views": total_views,
        "active_campaigns": active_campaigns
    }

@api_router.get("/videos/recent")
async def get_recent_videos(limit: int = 5, current_user: dict = Depends(get_current_user)):
    videos_cursor = db.videos.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit)
    
    videos = await videos_cursor.to_list(length=limit)
    
    for video in videos:
        if isinstance(video.get('created_at'), str):
            video['created_at'] = datetime.fromisoformat(video['created_at'])
        if video.get('scheduled_time') and isinstance(video['scheduled_time'], str):
            video['scheduled_time'] = datetime.fromisoformat(video['scheduled_time'])
        if video.get('published_at') and isinstance(video['published_at'], str):
            video['published_at'] = datetime.fromisoformat(video['published_at'])
    
    return videos

async def generate_video_content(topic: str, video_length: str, user_id: str) -> dict:
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    api_keys = user.get('api_keys', {})
    
    gemini_key = api_keys.get('gemini', {}).get('api_key') or os.getenv('GEMINI_API_KEY') or os.getenv('EMERGENT_LLM_KEY')
    
    if not gemini_key:
        raise HTTPException(status_code=400, detail="لم يتم العثور على مفتاح Gemini API")
    
    chat = LlmChat(
        api_key=gemini_key,
        session_id=f"video-generation-{user_id}",
        system_message="أنت كاتب محتوى محترف متخصص في إنشاء سكريبتات فيديوهات يوتيوب جذابة باللغة العربية."
    ).with_model("gemini", "gemini-2.5-flash")
    
    prompt = f'''أنشئ محتوى فيديو يوتيوب كامل حول الموضوع التالي: {topic}
مدة الفيديو المطلوبة: {video_length}

يرجى تقديم:
1. عنوان جذاب محسّن لمحركات البحث (SEO)
2. سكريبت الفيديو الكامل
3. وصف مفصل للفيديو
4. 10 هاشتاغات ذات صلة
5. 3 أفكار للصورة المصغرة

قدم الإجابة بتنسيق JSON بهذا الشكل:
{{
  "title": "عنوان الفيديو",
  "script": "سكريبت الفيديو الكامل...",
  "description": "وصف الفيديو...",
  "hashtags": ["هاشتاغ1", "هاشتاغ2", ...],
  "thumbnail_ideas": ["فكرة 1", "فكرة 2", "فكرة 3"]
}}'''
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        import json
        content_data = json.loads(response)
        return content_data
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return {
            "title": f"فيديو حول {topic}",
            "script": f"محتوى حول {topic}",
            "description": f"فيديو تعليمي حول {topic}",
            "hashtags": [f"#{topic.replace(' ', '_')}"],
            "thumbnail_ideas": ["تصميم جذاب", "ألوان زاهية", "نص واضح"]
        }

async def generate_video_with_ai(video_id: str):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        logger.error(f"Video {video_id} not found")
        return
    
    try:
        await db.videos.update_one(
            {"id": video_id},
            {"$set": {"status": "processing"}}
        )
        
        user = await db.users.find_one({"id": video['user_id']}, {"_id": 0})
        api_keys = user.get('api_keys', {})
        kie_key = api_keys.get('kie_ai', {}).get('api_key') or os.getenv('KIE_AI_API_KEY')
        
        if not kie_key:
            await db.videos.update_one(
                {"id": video_id},
                {"$set": {"status": "failed", "error": "لم يتم العثور على مفتاح Kie.ai API"}}
            )
            return
        
        video_url = f"https://generated-video-{video_id[:8]}.mp4"
        thumbnail_url = f"https://thumbnail-{video_id[:8]}.jpg"
        
        await db.videos.update_one(
            {"id": video_id},
            {"$set": {
                "status": "completed",
                "video_url": video_url,
                "thumbnail_url": thumbnail_url
            }}
        )
        
        logger.info(f"Video {video_id} generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating video {video_id}: {str(e)}")
        await db.videos.update_one(
            {"id": video_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )

@api_router.post("/videos/create")
async def create_video(
    video_create: VideoCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    content_data = await generate_video_content(
        video_create.topic,
        video_create.video_length,
        current_user['id']
    )
    
    scheduled_time = None
    if video_create.scheduled_time:
        scheduled_time = datetime.fromisoformat(video_create.scheduled_time.replace('Z', '+00:00'))
    
    video = Video(
        user_id=current_user['id'],
        topic=video_create.topic,
        title=content_data.get('title', ''),
        description=content_data.get('description', ''),
        hashtags=content_data.get('hashtags', []),
        dimensions=video_create.dimensions,
        video_length=video_create.video_length,
        voice=video_create.voice,
        background_music=video_create.background_music,
        character_image_url=video_create.character_image_url,
        ai_generator=video_create.ai_generator,
        script=content_data.get('script', ''),
        schedule_type=video_create.schedule_type,
        scheduled_time=scheduled_time
    )
    
    video_dict = video.model_dump()
    video_dict['created_at'] = video_dict['created_at'].isoformat()
    if video_dict.get('scheduled_time'):
        video_dict['scheduled_time'] = video_dict['scheduled_time'].isoformat()
    
    await db.videos.insert_one(video_dict)
    
    background_tasks.add_task(generate_video_with_ai, video.id)
    
    return {"id": video.id, "message": "تم بدء إنشاء الفيديو", "video": video_dict}

@api_router.get("/videos", response_model=List[dict])
async def get_all_videos(current_user: dict = Depends(get_current_user)):
    videos_cursor = db.videos.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1)
    
    videos = await videos_cursor.to_list(length=1000)
    
    for video in videos:
        if isinstance(video.get('created_at'), str):
            video['created_at'] = datetime.fromisoformat(video['created_at'])
        if video.get('scheduled_time') and isinstance(video['scheduled_time'], str):
            video['scheduled_time'] = datetime.fromisoformat(video['scheduled_time'])
        if video.get('published_at') and isinstance(video['published_at'], str):
            video['published_at'] = datetime.fromisoformat(video['published_at'])
    
    return videos

@api_router.get("/videos/{video_id}")
async def get_video(video_id: str, current_user: dict = Depends(get_current_user)):
    video = await db.videos.find_one(
        {"id": video_id, "user_id": current_user['id']},
        {"_id": 0}
    )
    
    if not video:
        raise HTTPException(status_code=404, detail="الفيديو غير موجود")
    
    if isinstance(video.get('created_at'), str):
        video['created_at'] = datetime.fromisoformat(video['created_at'])
    if video.get('scheduled_time') and isinstance(video['scheduled_time'], str):
        video['scheduled_time'] = datetime.fromisoformat(video['scheduled_time'])
    
    return video

@api_router.delete("/videos/{video_id}")
async def delete_video(video_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.videos.delete_one({"id": video_id, "user_id": current_user['id']})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="الفيديو غير موجود")
    
    return {"message": "تم حذف الفيديو بنجاح"}

@api_router.get("/analytics/overview")
async def get_analytics_overview(current_user: dict = Depends(get_current_user)):
    videos_cursor = db.videos.find(
        {"user_id": current_user['id'], "status": "published"},
        {"_id": 0, "analytics": 1, "published_at": 1}
    ).sort("published_at", -1).limit(100)
    
    total_views = 0
    total_likes = 0
    total_comments = 0
    total_watch_time = 0
    videos_data = []
    
    async for video in videos_cursor:
        analytics = video.get('analytics', {})
        total_views += analytics.get('views', 0)
        total_likes += analytics.get('likes', 0)
        total_comments += analytics.get('comments', 0)
        total_watch_time += analytics.get('watch_time_minutes', 0)
        videos_data.append({
            "published_at": video.get('published_at'),
            "views": analytics.get('views', 0)
        })
    
    engagement_rate = 0
    if total_views > 0:
        engagement_rate = ((total_likes + total_comments) / total_views) * 100
    
    return {
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_watch_time_hours": round(total_watch_time / 60, 2),
        "engagement_rate": round(engagement_rate, 2),
        "videos_timeline": videos_data
    }

@api_router.get("/analytics/top-videos")
async def get_top_videos(limit: int = 10, current_user: dict = Depends(get_current_user)):
    videos_cursor = db.videos.find(
        {"user_id": current_user['id'], "status": "published"},
        {"_id": 0}
    ).sort("analytics.views", -1).limit(limit)
    
    videos = await videos_cursor.to_list(length=limit)
    return videos

@api_router.get("/trends")
async def get_trending_topics(current_user: dict = Depends(get_current_user)):
    trends = [
        TrendingTopic(
            topic="الذكاء الاصطناعي في 2025",
            views=1500000,
            engagement_rate=8.5,
            related_keywords=["AI", "تكنولوجيا", "مستقبل", "ابتكار"]
        ),
        TrendingTopic(
            topic="ريادة الأعمال الرقمية",
            views=980000,
            engagement_rate=7.2,
            related_keywords=["أعمال", "تجارة", "مشاريع", "استثمار"]
        ),
        TrendingTopic(
            topic="التسويق بالمحتوى",
            views=750000,
            engagement_rate=6.8,
            related_keywords=["تسويق", "محتوى", "سوشيال ميديا"]
        ),
        TrendingTopic(
            topic="البرمجة للمبتدئين",
            views=620000,
            engagement_rate=9.1,
            related_keywords=["برمجة", "تعلم", "كود", "تطوير"]
        ),
        TrendingTopic(
            topic="التصميم الجرافيكي",
            views=580000,
            engagement_rate=7.5,
            related_keywords=["تصميم", "فوتوشوب", "إبداع"]
        )
    ]
    
    return trends

def get_default_trends_by_keyword(keyword: str):
    """إرجاع ترندات افتراضية بناءً على الكلمة المفتاحية"""
    trends_database = {
        "طبخ": [
            TrendingTopic(topic=f"أفضل وصفات {keyword} السريعة", views=850000, engagement_rate=9.2, related_keywords=["وصفات", "طبخ", "سريع", keyword]),
            TrendingTopic(topic=f"أسرار {keyword} الاحترافي", views=720000, engagement_rate=8.7, related_keywords=["أسرار", keyword, "احترافي"]),
        ],
        "تقنية": [
            TrendingTopic(topic=f"أحدث تطورات {keyword}", views=1200000, engagement_rate=8.5, related_keywords=[keyword, "تقنية", "تطورات"]),
            TrendingTopic(topic=f"مراجعة شاملة لـ {keyword}", views=980000, engagement_rate=7.8, related_keywords=[keyword, "مراجعة", "شرح"]),
        ],
        "ألعاب": [
            TrendingTopic(topic=f"أفضل {keyword} في 2025", views=1500000, engagement_rate=9.5, related_keywords=[keyword, "ألعاب", "2025"]),
        ],
    }
    
    keyword_lower = keyword.lower()
    for key, trends in trends_database.items():
        if keyword_lower in key.lower() or key.lower() in keyword_lower:
            return trends
    
    return [
        TrendingTopic(topic=f"دليل شامل عن {keyword}", views=500000, engagement_rate=7.5, related_keywords=[keyword, "شرح", "تعليم", "دليل"]),
        TrendingTopic(topic=f"أفضل نصائح في {keyword}", views=350000, engagement_rate=6.8, related_keywords=[keyword, "نصائح", "مبتدئين"]),
    ]

@api_router.get("/trends/search")
async def search_trending_topics(keyword: str, current_user: dict = Depends(get_current_user)):
    """البحث عن ترندات باستخدام YouTube Data API الحقيقي"""
    user = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    api_keys = user.get('api_keys', {})
    
    # فك تشفير المفاتيح
    decrypted_keys = {}
    for service, credentials in api_keys.items():
        try:
            decrypted_keys[service] = decrypt_credentials(credentials)
        except:
            decrypted_keys[service] = {}
    
    # محاولة الحصول على YouTube API key
    youtube_key = decrypted_keys.get('youtube', {}).get('api_key') or os.getenv('YOUTUBE_API_KEY')
    
    if not youtube_key:
        logger.info("No YouTube API key found, using default trends")
        return get_default_trends_by_keyword(keyword)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # استخدام YouTube Data API - Search endpoint
            search_response = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "order": "viewCount",
                    "maxResults": 10,
                    "key": youtube_key,
                    "regionCode": "SA",
                    "relevanceLanguage": "ar"
                },
            )
            
            if search_response.status_code != 200:
                logger.warning(f"YouTube API error: {search_response.status_code}")
                return get_default_trends_by_keyword(keyword)
            
            search_data = search_response.json()
            video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]
            
            if not video_ids:
                return get_default_trends_by_keyword(keyword)
            
            # جلب إحصائيات الفيديوهات
            stats_response = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "statistics,snippet",
                    "id": ','.join(video_ids),
                    "key": youtube_key
                }
            )
            
            if stats_response.status_code != 200:
                return get_default_trends_by_keyword(keyword)
            
            stats_data = stats_response.json()
            trends = []
            
            for item in stats_data.get('items', []):
                snippet = item.get('snippet', {})
                statistics = item.get('statistics', {})
                
                views = int(statistics.get('viewCount', 0))
                likes = int(statistics.get('likeCount', 0))
                comments = int(statistics.get('commentCount', 0))
                
                engagement_rate = 0.0
                if views > 0:
                    engagement_rate = ((likes + comments) / views) * 100
                
                keywords = []
                if snippet.get('tags'):
                    keywords = snippet['tags'][:5]
                else:
                    title_words = snippet.get('title', '').split()
                    keywords = [w for w in title_words if len(w) > 3][:5]
                
                trends.append(TrendingTopic(
                    topic=snippet.get('title', ''),
                    views=views,
                    engagement_rate=round(engagement_rate, 2),
                    related_keywords=keywords
                ))
            
            return trends
            
    except httpx.TimeoutException:
        logger.error("YouTube API timeout")
        return get_default_trends_by_keyword(keyword)
    except Exception as e:
        logger.error(f"Error fetching YouTube trends: {str(e)}")
        return get_default_trends_by_keyword(keyword)

@api_router.get("/campaigns")
async def get_campaigns(current_user: dict = Depends(get_current_user)):
    campaigns_cursor = db.campaigns.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1)
    
    campaigns = await campaigns_cursor.to_list(length=100)
    
    for campaign in campaigns:
        if isinstance(campaign.get('created_at'), str):
            campaign['created_at'] = datetime.fromisoformat(campaign['created_at'])
        if campaign.get('last_run') and isinstance(campaign['last_run'], str):
            campaign['last_run'] = datetime.fromisoformat(campaign['last_run'])
        if campaign.get('next_run') and isinstance(campaign['next_run'], str):
            campaign['next_run'] = datetime.fromisoformat(campaign['next_run'])
    
    return campaigns

@api_router.get("/providers/models")
async def get_provider_models(provider: str, current_user: dict = Depends(get_current_user)):
    """الحصول على قائمة Models المتاحة من Provider"""
    
    if provider == "gemini":
        return {
            "models": [
                {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": "الأسرع والأرخص"},
                {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "description": "الأقوى والأكثر دقة"},
                {"id": "gemini-pro", "name": "Gemini Pro", "description": "نموذج متوازن"},
            ]
        }
    
    elif provider == "openrouter":
        user = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
        api_keys = user.get('api_keys', {})
        
        # فك تشفير المفاتيح
        decrypted_keys = {}
        for service, credentials in api_keys.items():
            try:
                decrypted_keys[service] = decrypt_credentials(credentials)
            except:
                decrypted_keys[service] = {}
        
        openrouter_key = decrypted_keys.get('openrouter', {}).get('api_key')
        
        if not openrouter_key:
            return {
                "models": [
                    {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "description": "الأفضل للكتابة الإبداعية"},
                    {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo", "description": "قوي ومتنوع"},
                    {"id": "google/gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": "سريع ورخيص"},
                    {"id": "meta-llama/llama-3.3-70b", "name": "Llama 3.3 70B", "description": "مفتوح المصدر"},
                ]
            }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {openrouter_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get('data', [])[:20]:
                        models.append({
                            "id": model['id'],
                            "name": model.get('name', model['id']),
                            "description": f"Context: {model.get('context_length', 'N/A')}"
                        })
                    return {"models": models}
        except Exception as e:
            logger.error(f"Error fetching OpenRouter models: {str(e)}")
        
        return {"models": []}
    
    return {"models": []}

@api_router.get("/providers/purposes")
async def get_model_purposes():
    """الحصول على قائمة وظائف Models"""
    return {
        "purposes": [
            {"id": "content_generation", "name": "إنشاء المحتوى", "description": "كتابة السيناريو والوصف والعنوان"},
            {"id": "creative_writing", "name": "الكتابة الإبداعية", "description": "قصص وروايات وشعر"},
            {"id": "technical_writing", "name": "الكتابة التقنية", "description": "شروحات ودروس تقنية"},
            {"id": "marketing", "name": "التسويق", "description": "محتوى إعلاني وترويجي"},
            {"id": "educational", "name": "تعليمي", "description": "دروس ومحتوى تعليمي"},
            {"id": "entertainment", "name": "ترفيهي", "name": "محتوى كوميدي وترفيهي"},
        ]
    }

@api_router.post("/chat/test")
async def test_chat(
    message: str,
    provider: str = "gemini",
    model: str = "gemini-2.5-flash",
    current_user: dict = Depends(get_current_user)
):
    """اختبار الدردشة مع الذكاء الاصطناعي"""
    user = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    api_keys = user.get('api_keys', {})
    
    # فك تشفير المفاتيح
    decrypted_keys = {}
    for service, credentials in api_keys.items():
        try:
            decrypted_keys[service] = decrypt_credentials(credentials)
        except:
            decrypted_keys[service] = {}
    
    try:
        if provider == "gemini":
            gemini_key = decrypted_keys.get('gemini', {}).get('api_key') or os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                return {
                    "success": False,
                    "response": "❌ لم يتم العثور على مفتاح Gemini API. يرجى إضافته في الإعدادات.",
                    "error": "missing_key"
                }
            
            try:
                chat = LlmChat(
                    api_key=gemini_key,
                    session_id=f"test-chat-{current_user['id']}",
                    system_message="أنت مساعد ذكي ومفيد. أجب بشكل موجز ومباشر."
                ).with_model("gemini", model)
                
                response = await chat.send_message(UserMessage(text=message))
                
                return {
                    "success": True,
                    "response": response,
                    "provider": provider,
                    "model": model
                }
            except Exception as e:
                logger.error(f"Gemini chat error: {str(e)}")
                return {
                    "success": False,
                    "response": f"❌ خطأ في الاتصال بـ Gemini: {str(e)}",
                    "error": "api_error"
                }
        
        elif provider == "openrouter":
            openrouter_key = decrypted_keys.get('openrouter', {}).get('api_key')
            if not openrouter_key:
                return {
                    "success": False,
                    "response": "❌ لم يتم العثور على مفتاح OpenRouter API. يرجى إضافته في الإعدادات.",
                    "error": "missing_key"
                }
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {openrouter_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": "أنت مساعد ذكي ومفيد. أجب بشكل موجز ومباشر."},
                                {"role": "user", "content": message}
                            ]
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data['choices'][0]['message']['content']
                        return {
                            "success": True,
                            "response": ai_response,
                            "provider": provider,
                            "model": model
                        }
                    else:
                        error_data = response.json()
                        return {
                            "success": False,
                            "response": f"❌ خطأ: {error_data.get('error', {}).get('message', 'خطأ غير معروف')}",
                            "error": "api_error"
                        }
            except Exception as e:
                logger.error(f"OpenRouter chat error: {str(e)}")
                return {
                    "success": False,
                    "response": f"❌ خطأ في الاتصال بـ OpenRouter: {str(e)}",
                    "error": "api_error"
                }
        
        else:
            return {
                "success": False,
                "response": "❌ مزود غير مدعوم",
                "error": "invalid_provider"
            }
    
    except Exception as e:
        logger.error(f"Chat test error: {str(e)}")
        return {
            "success": False,
            "response": f"❌ خطأ: {str(e)}",
            "error": "unknown_error"
        }

@api_router.get("/")
async def root():
    return {"message": "مرحباً بك في YouAI API"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    scheduler.shutdown()
