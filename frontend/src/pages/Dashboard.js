import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Play, Eye, FileVideo, Clock, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentVideos, setRecentVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsRes, videosRes] = await Promise.all([
        api.dashboard.getStats(),
        api.dashboard.getRecentVideos(5)
      ]);
      setStats(statsRes.data);
      setRecentVideos(videosRes.data);
    } catch (error) {
      toast.error('فشل تحميل بيانات لوحة التحكم');
    } finally {
      setLoading(false);
    }
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
      <span className={`px-3 py-1 rounded-full text-xs font-tajawal font-bold border ${badges[status] || badges.pending}`}>
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
    <div className="space-y-8" data-testid="dashboard-container">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-cairo font-bold text-white">لوحة التحكم</h1>
          <p className="text-zinc-400 font-tajawal mt-2">مرحباً بك في منصة يو.آي</p>
        </div>
        <Link to="/create">
          <Button className="bg-orange-500 hover:bg-orange-600 text-white font-cairo font-bold shadow-lg shadow-orange-500/20 hover:shadow-orange-500/40 transition-all duration-300" data-testid="create-video-button">
            <Play className="ml-2 h-5 w-5" fill="currentColor" />
            إنشاء فيديو جديد
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-zinc-900 border-zinc-800 hover:border-orange-500/50 transition-all duration-300" data-testid="stat-total-videos">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-tajawal text-zinc-400">إجمالي الفيديوهات</CardTitle>
            <FileVideo className="h-5 w-5 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-manrope font-bold text-white">{stats?.total_videos || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800 hover:border-lime-500/50 transition-all duration-300" data-testid="stat-published-videos">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-tajawal text-zinc-400">منشور</CardTitle>
            <Play className="h-5 w-5 text-lime-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-manrope font-bold text-white">{stats?.published_videos || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800 hover:border-blue-500/50 transition-all duration-300" data-testid="stat-total-views">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-tajawal text-zinc-400">إجمالي المشاهدات</CardTitle>
            <Eye className="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-manrope font-bold text-white">{stats?.total_views?.toLocaleString('ar-EG') || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800 hover:border-purple-500/50 transition-all duration-300" data-testid="stat-active-campaigns">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-tajawal text-zinc-400">حملات نشطة</CardTitle>
            <TrendingUp className="h-5 w-5 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-manrope font-bold text-white">{stats?.active_campaigns || 0}</div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-2xl font-cairo font-bold text-white flex items-center">
            <Clock className="ml-3 h-6 w-6 text-orange-500" />
            الفيديوهات الأخيرة
          </CardTitle>
        </CardHeader>
        <CardContent>
          {recentVideos.length === 0 ? (
            <div className="text-center py-12">
              <FileVideo className="h-12 w-12 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500 font-tajawal">لم يتم إنشاء فيديوهات بعد</p>
              <Link to="/create">
                <Button className="mt-4 bg-orange-500 hover:bg-orange-600 font-cairo">
                  إنشاء أول فيديو
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {recentVideos.map((video) => (
                <div key={video.id} className="flex items-center justify-between p-4 bg-zinc-800/50 rounded-xl border border-zinc-800 hover:border-orange-500/30 transition-all duration-300">
                  <div className="flex-1">
                    <h3 className="font-cairo font-bold text-white mb-1">{video.title || video.topic}</h3>
                    <p className="text-sm text-zinc-400 font-tajawal">{video.topic}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    {getStatusBadge(video.status)}
                    <span className="text-xs text-zinc-500 font-manrope" dir="ltr">
                      {new Date(video.created_at).toLocaleDateString('ar-EG')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
