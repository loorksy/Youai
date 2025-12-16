import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Play, Image as ImageIcon, Clock, Sparkles } from 'lucide-react';

export default function CreateVideo() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    topic: '',
    dimensions: '16:9',
    video_length: '60 ثانية',
    ai_generator: 'sora2',
    voice: null,
    background_music: false,
    character_image_url: null,
    schedule_type: 'immediate',
    scheduled_time: null
  });
  const [characterImage, setCharacterImage] = useState(null);
  const [videoDuration, setVideoDuration] = useState(60);
  const [autoDuration, setAutoDuration] = useState(true);

  const handleCharacterImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('حجم الصورة يجب أن يكون أقل من 5 ميجابايت');
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        setCharacterImage(e.target.result);
        setFormData({ ...formData, character_image_url: e.target.result });
      };
      reader.readAsDataURL(file);
    }
  };

  const removeCharacterImage = () => {
    setCharacterImage(null);
    setFormData({ ...formData, character_image_url: null });
  };

  const getMaxDuration = () => {
    return formData.ai_generator === 'sora2' ? 60 : 120;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.topic.trim()) {
      toast.error('يرجى إدخال موضوع الفيديو');
      return;
    }

    setLoading(true);
    try {
      const response = await api.videos.create(formData);
      toast.success('تم بدء إنشاء الفيديو بنجاح');
      navigate('/videos');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'فشل إنشاء الفيديو');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8" data-testid="create-video-page">
      <div>
        <h1 className="text-4xl font-cairo font-bold text-white flex items-center">
          <Sparkles className="ml-3 h-10 w-10 text-orange-500" />
          إنشاء فيديو جديد
        </h1>
        <p className="text-zinc-400 font-tajawal mt-2">
          أنشئ فيديوهات يوتيوب احترافية باستخدام الذكاء الاصطناعي
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-xl font-cairo font-bold text-white">
              معلومات المحتوى
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="topic" className="text-right block font-tajawal text-zinc-300">
                موضوع الفيديو *
              </Label>
              <Input
                id="topic"
                value={formData.topic}
                onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                className="bg-zinc-800/50 border-zinc-700 text-white text-right font-tajawal"
                placeholder="مثال: كيفية استخدام الذكاء الاصطناعي في التسويق"
                required
                data-testid="topic-input"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-right block font-tajawal text-zinc-300">
                رفع صورة الشخصية (اختياري)
              </Label>
              <div className="border-2 border-dashed border-zinc-700 rounded-xl p-6 text-center hover:border-orange-500/50 transition-all duration-300">
                {!characterImage ? (
                  <div>
                    <ImageIcon className="h-12 w-12 text-zinc-600 mx-auto mb-3" />
                    <p className="text-zinc-400 font-tajawal mb-3">اسحب وأفلت الصورة هنا أو انقر للاختيار</p>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleCharacterImageUpload}
                      className="hidden"
                      id="character-upload"
                      data-testid="character-upload-input"
                    />
                    <label htmlFor="character-upload">
                      <Button type="button" variant="outline" className="border-zinc-700 text-white hover:bg-zinc-800 font-cairo" asChild>
                        <span>اختر صورة</span>
                      </Button>
                    </label>
                    <p className="text-xs text-zinc-500 font-tajawal mt-2">PNG, JPG, WEBP (حد أقصى 5MB)</p>
                  </div>
                ) : (
                  <div className="relative">
                    <img src={characterImage} alt="معاينة الشخصية" className="max-h-48 mx-auto rounded-lg" />
                    <Button
                      type="button"
                      onClick={removeCharacterImage}
                      variant="destructive"
                      size="sm"
                      className="absolute top-2 left-2 font-cairo"
                      data-testid="remove-character-image"
                    >
                      ✖ إزالة
                    </Button>
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label className="text-right block font-tajawal text-zinc-300">
                  أبعاد الفيديو
                </Label>
                <Select
                  value={formData.dimensions}
                  onValueChange={(value) => setFormData({ ...formData, dimensions: value })}
                >
                  <SelectTrigger className="bg-zinc-800/50 border-zinc-700 text-white text-right font-tajawal" data-testid="dimensions-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="16:9">16:9 (أفقي - YouTube)</SelectItem>
                    <SelectItem value="9:16">9:16 (عمودي - Shorts)</SelectItem>
                    <SelectItem value="1:1">1:1 (مربع)</SelectItem>
                    <SelectItem value="4:5">4:5 (Instagram)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-right block font-tajawal text-zinc-300">
                  طول الفيديو
                </Label>
                <Select
                  value={formData.video_length}
                  onValueChange={(value) => setFormData({ ...formData, video_length: value })}
                >
                  <SelectTrigger className="bg-zinc-800/50 border-zinc-700 text-white text-right font-tajawal" data-testid="length-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30 ثانية">30 ثانية</SelectItem>
                    <SelectItem value="60 ثانية">60 ثانية</SelectItem>
                    <SelectItem value="90 ثانية">90 ثانية</SelectItem>
                    <SelectItem value="3 دقائق">3 دقائق</SelectItem>
                    <SelectItem value="5 دقائق">5 دقائق</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-right block font-tajawal text-zinc-300">
                منشئ الفيديو بالذكاء الاصطناعي
              </Label>
              <Select
                value={formData.ai_generator}
                onValueChange={(value) => setFormData({ ...formData, ai_generator: value })}
              >
                <SelectTrigger className="bg-zinc-800/50 border-zinc-700 text-white text-right font-tajawal" data-testid="ai-generator-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sora2">Sora 2 (OpenAI)</SelectItem>
                  <SelectItem value="veo3">Veo 3 (Google)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-xl font-cairo font-bold text-white">
              إعدادات إضافية
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="text-right">
                <Label className="font-tajawal text-zinc-300">موسيقى خلفية</Label>
                <p className="text-sm text-zinc-500 font-tajawal">إضافة موسيقى خلفية للفيديو</p>
              </div>
              <Switch
                checked={formData.background_music}
                onCheckedChange={(checked) => setFormData({ ...formData, background_music: checked })}
                data-testid="music-switch"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-right block font-tajawal text-zinc-300">
                نوع الجدولة
              </Label>
              <Select
                value={formData.schedule_type}
                onValueChange={(value) => setFormData({ ...formData, schedule_type: value })}
              >
                <SelectTrigger className="bg-zinc-800/50 border-zinc-700 text-white text-right font-tajawal" data-testid="schedule-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="immediate">النشر فوراً</SelectItem>
                  <SelectItem value="scheduled">جدولة لوقت محدد</SelectItem>
                  <SelectItem value="recurring">جدولة متكررة</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {formData.schedule_type === 'scheduled' && (
              <div className="space-y-2">
                <Label htmlFor="scheduled_time" className="text-right block font-tajawal text-zinc-300">
                  وقت النشر المحدد
                </Label>
                <Input
                  id="scheduled_time"
                  type="datetime-local"
                  value={formData.scheduled_time || ''}
                  onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
                  className="bg-zinc-800/50 border-zinc-700 text-white text-right font-tajawal"
                  data-testid="scheduled-time-input"
                />
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex gap-4">
          <Button
            type="button"
            onClick={() => navigate('/dashboard')}
            variant="outline"
            className="flex-1 border-zinc-700 text-white hover:bg-zinc-800 font-cairo"
            data-testid="cancel-button"
          >
            إلغاء
          </Button>
          <Button
            type="submit"
            disabled={loading}
            className="flex-1 bg-orange-500 hover:bg-orange-600 text-white font-cairo font-bold shadow-lg shadow-orange-500/20 hover:shadow-orange-500/40 transition-all duration-300"
            data-testid="submit-button"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white ml-2"></div>
                جاري الإنشاء...
              </>
            ) : (
              <>
                <Play className="ml-2 h-5 w-5" fill="currentColor" />
                إنشاء الفيديو
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
