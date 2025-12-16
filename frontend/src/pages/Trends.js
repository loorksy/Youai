import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { TrendingUp, Eye, Hash, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

export default function Trends() {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadTrends();
  }, []);

  const loadTrends = async () => {
    try {
      const response = await api.trends.get();
      setTrends(response.data);
    } catch (error) {
      toast.error('فشل تحميل الترندات');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchKeyword.trim()) {
      toast.error('يرجى إدخال كلمة بحث');
      return;
    }

    setSearching(true);
    try {
      const response = await api.trends.search(searchKeyword);
      setTrends(response.data);
      toast.success(`تم العثور على ${response.data.length} ترند`);
    } catch (error) {
      toast.error('فشل البحث عن الترندات');
    } finally {
      setSearching(false);
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
    <div className="space-y-8" data-testid="trends-page">
      <div>
        <h1 className="text-4xl font-cairo font-bold text-white flex items-center">
          <TrendingUp className="ml-3 h-10 w-10 text-orange-500" />
          الترندات
        </h1>
        <p className="text-zinc-400 font-tajawal mt-2">
          اكتشف الموضوعات الرائجة وأفكار الفيديوهات
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {trends.map((trend, index) => (
          <Card key={index} className="bg-zinc-900 border-zinc-800 hover:border-orange-500/30 transition-all duration-300">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500/20 to-orange-600/10 border border-orange-500/30 flex items-center justify-center">
                      <span className="text-xl font-manrope font-bold text-orange-500">#{index + 1}</span>
                    </div>
                    <CardTitle className="text-xl font-cairo font-bold text-white">
                      {trend.topic}
                    </CardTitle>
                  </div>
                  <div className="flex gap-4 text-sm text-zinc-400 font-tajawal mt-3">
                    <span className="flex items-center gap-1">
                      <Eye className="h-4 w-4" />
                      {trend.views?.toLocaleString('ar-EG')} مشاهدة
                    </span>
                    <span className="flex items-center gap-1">
                      <TrendingUp className="h-4 w-4" />
                      {trend.engagement_rate}% تفاعل
                    </span>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Hash className="h-4 w-4 text-lime-500" />
                  <span className="text-sm font-tajawal font-bold text-zinc-300">الكلمات المفتاحية</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {trend.related_keywords?.map((keyword, kidx) => (
                    <span
                      key={kidx}
                      className="px-3 py-1 rounded-full text-xs font-tajawal font-bold bg-zinc-800 text-zinc-300 border border-zinc-700"
                    >
                      #{keyword}
                    </span>
                  ))}
                </div>
              </div>
              <Button
                onClick={() => navigate('/create', { state: { topic: trend.topic } })}
                className="w-full bg-orange-500 hover:bg-orange-600 text-white font-cairo shadow-lg shadow-orange-500/10 hover:shadow-orange-500/20 transition-all duration-300"
                data-testid={`use-trend-${index}`}
              >
                <Sparkles className="ml-2 h-4 w-4" />
                استخدم هذا الترند
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
