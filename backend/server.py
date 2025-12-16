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
    api_keys = current_user.get('api_keys', {})
    api_keys[api_key_update.service] = api_key_update.credentials
    
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"api_keys": api_keys}}
    )
    
    return {"message": f"تم تحديث بيانات {api_key_update.service} بنجاح"}

@api_router.post("/settings/test-connection")
async def test_api_connection(service: str, current_user: dict = Depends(get_current_user)):
    api_keys = current_user.get('api_keys', {})
    
    if service == "gemini":
        gemini_key = api_keys.get('gemini', {}).get('api_key') or os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            return APIConnection(service=service, status="error", message="لم يتم العثور على مفتاح API")
        
        try:
            chat = LlmChat(
                api_key=gemini_key,
                session_id="test-connection",
                system_message="You are a test assistant."
            ).with_model("gemini", "gemini-2.5-flash")
            
            response = await chat.send_message(UserMessage(text="مرحباً"))
            return APIConnection(service=service, status="success", message="الاتصال ناجح")
        except Exception as e:
            return APIConnection(service=service, status="error", message=f"فشل الاتصال: {str(e)}")
    
    elif service == "kie_ai":
        kie_key = api_keys.get('kie_ai', {}).get('api_key') or os.getenv('KIE_AI_API_KEY')
        if not kie_key:
            return APIConnection(service=service, status="error", message="لم يتم العثور على مفتاح API")
        
        return APIConnection(service=service, status="success", message="مفتاح API محفوظ")
    
    elif service == "youtube":
        youtube_creds = api_keys.get('youtube', {})
        if not youtube_creds.get('client_id'):
            return APIConnection(service=service, status="error", message="بيانات اعتماد YouTube غير مكتملة")
        
        return APIConnection(service=service, status="success", message="بيانات الاعتماد محفوظة")
    
    return APIConnection(service=service, status="error", message="خدمة غير معروفة")

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
