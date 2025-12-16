import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { BarChart3, Eye, ThumbsUp, MessageCircle, Clock, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [topVideos, setTopVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [overviewRes, topVideosRes] = await Promise.all([
        api.analytics.getOverview(),
        api.analytics.getTopVideos(5)
      ]);
      setAnalytics(overviewRes.data);
      setTopVideos(topVideosRes.data);
    } catch (error) {
      toast.error('فشل تحميل التحليلات');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="analytics-page">
      <div>
        <h1 className="text-4xl font-cairo font-bold text-white flex items-center">
          <BarChart3 className="ml-3 h-10 w-10 text-orange-500" />
          التحليلات
        </h1>
        <p className="text-zinc-400 font-tajawal mt-2">
          تحليل أداء الفيديوهات والتفاعل
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-zinc-900 border-zinc-800 hover:border-blue-500/50 transition-all duration-300" data-testid="analytics-views">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-tajawal text-zinc-400">إجمالي المشاهدات</CardTitle>
            <Eye className="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-manrope font-bold text-white">{analytics?.total_views?.toLocaleString('ar-EG') || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800 hover:border-lime-500/50 transition-all duration-300" data-testid="analytics-likes">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-tajawal text-zinc-400">الإعجابات</CardTitle>
            <ThumbsUp className="h-5 w-5 text-lime-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-manrope font-bold text-white">{analytics?.total_likes?.toLocaleString('ar-EG') || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800 hover:border-purple-500/50 transition-all duration-300" data-testid="analytics-comments">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-tajawal text-zinc-400">التعليقات</CardTitle>
            <MessageCircle className="h-5 w-5 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-manrope font-bold text-white">{analytics?.total_comments?.toLocaleString('ar-EG') || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800 hover:border-orange-500/50 transition-all duration-300" data-testid="analytics-engagement">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-tajawal text-zinc-400">معدل التفاعل</CardTitle>
            <TrendingUp className="h-5 w-5 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-manrope font-bold text-white">{analytics?.engagement_rate || 0}%</div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-2xl font-cairo font-bold text-white flex items-center">
            <TrendingUp className="ml-3 h-6 w-6 text-orange-500" />
            أفضل الفيديوهات أداءً
          </CardTitle>
        </CardHeader>
        <CardContent>
          {topVideos.length === 0 ? (
            <div className="text-center py-12">
              <BarChart3 className="h-12 w-12 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500 font-tajawal">لا توجد بيانات تحليلية بعد</p>
            </div>
          ) : (
            <div className="space-y-4">
              {topVideos.map((video, index) => (
                <div key={video.id} className="flex items-center gap-4 p-4 bg-zinc-800/50 rounded-xl border border-zinc-800 hover:border-orange-500/30 transition-all duration-300">
                  <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-orange-500/20 to-orange-600/10 border border-orange-500/30 flex items-center justify-center">
                    <span className="text-2xl font-manrope font-bold text-orange-500">#{index + 1}</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-cairo font-bold text-white mb-1">{video.title || video.topic}</h3>
                    <div className="flex gap-4 text-sm text-zinc-400 font-tajawal">
                      <span className="flex items-center gap-1">
                        <Eye className="h-4 w-4" />
                        {video.analytics?.views?.toLocaleString('ar-EG') || 0}
                      </span>
                      <span className="flex items-center gap-1">
                        <ThumbsUp className="h-4 w-4" />
                        {video.analytics?.likes?.toLocaleString('ar-EG') || 0}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageCircle className="h-4 w-4" />
                        {video.analytics?.comments?.toLocaleString('ar-EG') || 0}
                      </span>
                    </div>
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
