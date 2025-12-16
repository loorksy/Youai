import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { FileVideo, Trash2, Clock, CheckCircle2, AlertCircle, Loader } from 'lucide-react';
import { toast } from 'sonner';

export default function Videos() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    try {
      const response = await api.videos.getAll();
      setVideos(response.data);
    } catch (error) {
      toast.error('فشل تحميل الفيديوهات');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (videoId) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا الفيديو؟')) {
      return;
    }

    setDeletingId(videoId);
    try {
      await api.videos.delete(videoId);
      setVideos(videos.filter(v => v.id !== videoId));
      toast.success('تم حذف الفيديو بنجاح');
    } catch (error) {
      toast.error('فشل حذف الفيديو');
    } finally {
      setDeletingId(null);
    }
  };

  const getStatusIcon = (status) => {
    const icons = {
      completed: <CheckCircle2 className="h-5 w-5 text-lime-500" />,
      processing: <Loader className="h-5 w-5 text-orange-500 animate-spin" />,
      pending: <Clock className="h-5 w-5 text-yellow-500" />,
      failed: <AlertCircle className="h-5 w-5 text-red-500" />,
      published: <CheckCircle2 className="h-5 w-5 text-blue-500" />
    };
    return icons[status] || icons.pending;
  };

  const getStatusBadge = (status) => {
    const badges = {
      completed: 'bg-lime-500/20 text-lime-500 border-lime-500/30',
      processing: 'bg-orange-500/20 text-orange-500 border-orange-500/30',
      pending: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
      failed: 'bg-red-500/20 text-red-500 border-red-500/30',
      published: 'bg-blue-500/20 text-blue-500 border-blue-500/30'
    };
    
    const statusText = {
      completed: 'مكتمل',
      processing: 'جاري المعالجة',
      pending: 'قيد الانتظار',
      failed: 'فشل',
      published: 'منشور'
    };

    return (
      <span className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-tajawal font-bold border ${badges[status] || badges.pending}`}>
        {getStatusIcon(status)}
        {statusText[status] || status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="videos-page">
      <div>
        <h1 className="text-4xl font-cairo font-bold text-white flex items-center">
          <FileVideo className="ml-3 h-10 w-10 text-orange-500" />
          قائمة النشر
        </h1>
        <p className="text-zinc-400 font-tajawal mt-2">
          إدارة جميع الفيديوهات المجدولة والمنشورة
        </p>
      </div>

      {videos.length === 0 ? (
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="py-16">
            <div className="text-center">
              <FileVideo className="h-16 w-16 text-zinc-700 mx-auto mb-4" />
              <h3 className="text-xl font-cairo font-bold text-white mb-2">لا توجد فيديوهات بعد</h3>
              <p className="text-zinc-500 font-tajawal mb-6">ابدأ بإنشاء أول فيديو لك</p>
              <Button onClick={() => window.location.href = '/create'} className="bg-orange-500 hover:bg-orange-600 font-cairo">
                إنشاء فيديو جديد
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {videos.map((video) => (
            <Card key={video.id} className="bg-zinc-900 border-zinc-800 hover:border-orange-500/30 transition-all duration-300">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl font-cairo font-bold text-white mb-2">
                      {video.title || video.topic}
                    </CardTitle>
                    <p className="text-zinc-400 font-tajawal text-sm">{video.topic}</p>
                  </div>
                  {getStatusBadge(video.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex gap-4 text-sm text-zinc-400 font-tajawal">
                    <span>الطول: {video.video_length}</span>
                    <span>الأبعاد: {video.dimensions}</span>
                    <span>المنشئ: {video.ai_generator === 'sora2' ? 'Sora 2' : 'Veo 3'}</span>
                  </div>
                  <Button
                    onClick={() => handleDelete(video.id)}
                    disabled={deletingId === video.id}
                    variant="outline"
                    size="sm"
                    className="border-red-500/30 text-red-500 hover:bg-red-500/10 hover:border-red-500 font-cairo"
                    data-testid={`delete-video-${video.id}`}
                  >
                    <Trash2 className="ml-2 h-4 w-4" />
                    {deletingId === video.id ? 'جاري الحذف...' : 'حذف'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
