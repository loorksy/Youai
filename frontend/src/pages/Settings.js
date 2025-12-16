import React, { useState } from 'react';
import { api } from '../utils/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { Settings as SettingsIcon, Key, CheckCircle2, XCircle, Youtube, Database, Table } from 'lucide-react';

export default function Settings() {
  const [loading, setLoading] = useState({});
  const [connections, setConnections] = useState({});
  
  const [apiKeys, setApiKeys] = useState({
    gemini: { api_key: '' },
    kie_ai: { api_key: '' },
    youtube: { client_id: '', client_secret: '', redirect_uri: '' },
    google_drive: { credentials_json: '' },
    google_sheets: { sheet_id: '' }
  });

  const handleInputChange = (service, field, value) => {
    setApiKeys(prev => ({
      ...prev,
      [service]: {
        ...prev[service],
        [field]: value
      }
    }));
  };

  const handleSave = async (service) => {
    setLoading(prev => ({ ...prev, [service]: true }));
    try {
      await api.settings.updateApiKeys(service, apiKeys[service]);
      toast.success(`تم حفظ ${getServiceName(service)} بنجاح`);
    } catch (error) {
      toast.error(`فشل حفظ ${getServiceName(service)}`);
    } finally {
      setLoading(prev => ({ ...prev, [service]: false }));
    }
  };

  const handleTestConnection = async (service) => {
    setLoading(prev => ({ ...prev, [`${service}_test`]: true }));
    try {
      const response = await api.settings.testConnection(service);
      setConnections(prev => ({ ...prev, [service]: response.data }));
      
      if (response.data.status === 'success') {
        toast.success(response.data.message);
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error('فشل اختبار الاتصال');
      setConnections(prev => ({ 
        ...prev, 
        [service]: { status: 'error', message: 'فشل الاتصال' } 
      }));
    } finally {
      setLoading(prev => ({ ...prev, [`${service}_test`]: false }));
    }
  };

  const getServiceName = (service) => {
    const names = {
      gemini: 'Google Gemini API',
      kie_ai: 'Kie.ai API',
      youtube: 'YouTube API',
      google_drive: 'Google Drive API',
      google_sheets: 'Google Sheets API'
    };
    return names[service] || service;
  };

  const getStatusBadge = (status) => {
    if (!status) return null;
    
    const configs = {
      success: {
        icon: CheckCircle2,
        className: 'text-lime-500 bg-lime-500/10 border-lime-500/30',
        text: 'متصل'
      },
      error: {
        icon: XCircle,
        className: 'text-red-500 bg-red-500/10 border-red-500/30',
        text: 'غير متصل'
      }
    };
    
    const config = configs[status.status];
    if (!config) return null;
    
    const Icon = config.icon;
    
    return (
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${config.className}`}>
        <Icon className="h-4 w-4" />
        <span className="text-sm font-tajawal font-bold">{config.text}</span>
      </div>
    );
  };

  return (
    <div className="space-y-8" data-testid="settings-page">
      <div>
        <h1 className="text-4xl font-cairo font-bold text-white flex items-center">
          <SettingsIcon className="ml-3 h-10 w-10 text-orange-500" />
          الإعدادات
        </h1>
        <p className="text-zinc-400 font-tajawal mt-2">
          إدارة اتصالات API والإعدادات العامة
        </p>
      </div>

      <Tabs defaultValue="ai" className="space-y-6">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="ai" className="font-tajawal data-[state=active]:bg-orange-500/10 data-[state=active]:text-orange-500">
            الذكاء الاصطناعي
          </TabsTrigger>
          <TabsTrigger value="youtube" className="font-tajawal data-[state=active]:bg-orange-500/10 data-[state=active]:text-orange-500">
            YouTube
          </TabsTrigger>
          <TabsTrigger value="google" className="font-tajawal data-[state=active]:bg-orange-500/10 data-[state=active]:text-orange-500">
            Google Services
          </TabsTrigger>
        </TabsList>

        <TabsContent value="ai" className="space-y-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl font-cairo font-bold text-white flex items-center">
                    <Key className="ml-2 h-5 w-5 text-orange-500" />
                    Google Gemini API
                  </CardTitle>
                  <CardDescription className="text-zinc-400 font-tajawal">
                    لإنشاء محتوى الفيديو والسكريبتات
                  </CardDescription>
                </div>
                {getStatusBadge(connections.gemini)}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-right block font-tajawal text-zinc-300">
                  API Key
                </Label>
                <Input
                  type="password"
                  value={apiKeys.gemini.api_key}
                  onChange={(e) => handleInputChange('gemini', 'api_key', e.target.value)}
                  className="bg-zinc-800/50 border-zinc-700 text-white text-right font-mono"
                  placeholder="AIzaSy..."
                  data-testid="gemini-api-key-input"
                />
                <a 
                  href="https://aistudio.google.com/app/apikey" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-orange-500 hover:text-orange-400 text-sm font-tajawal inline-flex items-center gap-1"
                >
                  🔗 احصل على المفتاح من Google AI Studio
                </a>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={() => handleSave('gemini')}
                  disabled={loading.gemini}
                  className="flex-1 bg-orange-500 hover:bg-orange-600 font-cairo"
                  data-testid="gemini-save-button"
                >
                  {loading.gemini ? 'جاري الحفظ...' : 'حفظ'}
                </Button>
                <Button
                  onClick={() => handleTestConnection('gemini')}
                  disabled={loading.gemini_test}
                  variant="outline"
                  className="flex-1 border-zinc-700 text-white hover:bg-zinc-800 font-cairo"
                  data-testid="gemini-test-button"
                >
                  {loading.gemini_test ? 'جاري الاختبار...' : 'اختبار الاتصال'}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl font-cairo font-bold text-white flex items-center">
                    <Key className="ml-2 h-5 w-5 text-orange-500" />
                    Kie.ai API
                  </CardTitle>
                  <CardDescription className="text-zinc-400 font-tajawal">
                    لإنشاء الفيديوهات باستخدام Sora2 و Veo3
                  </CardDescription>
                </div>
                {getStatusBadge(connections.kie_ai)}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-right block font-tajawal text-zinc-300">
                  API Key
                </Label>
                <Input
                  type="password"
                  value={apiKeys.kie_ai.api_key}
                  onChange={(e) => handleInputChange('kie_ai', 'api_key', e.target.value)}
                  className="bg-zinc-800/50 border-zinc-700 text-white text-right font-mono"
                  placeholder="kie_..."
                  data-testid="kie-api-key-input"
                />
                <a 
                  href="https://kie.ai/dashboard/api-keys" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-orange-500 hover:text-orange-400 text-sm font-tajawal inline-flex items-center gap-1"
                >
                  🔗 احصل على المفتاح من Kie.ai Dashboard
                </a>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={() => handleSave('kie_ai')}
                  disabled={loading.kie_ai}
                  className="flex-1 bg-orange-500 hover:bg-orange-600 font-cairo"
                  data-testid="kie-save-button"
                >
                  {loading.kie_ai ? 'جاري الحفظ...' : 'حفظ'}
                </Button>
                <Button
                  onClick={() => handleTestConnection('kie_ai')}
                  disabled={loading.kie_ai_test}
                  variant="outline"
                  className="flex-1 border-zinc-700 text-white hover:bg-zinc-800 font-cairo"
                  data-testid="kie-test-button"
                >
                  {loading.kie_ai_test ? 'جاري الاختبار...' : 'اختبار الاتصال'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="youtube" className="space-y-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl font-cairo font-bold text-white flex items-center">
                    <Youtube className="ml-2 h-5 w-5 text-orange-500" />
                    YouTube Data API
                  </CardTitle>
                  <CardDescription className="text-zinc-400 font-tajawal">
                    لرفع الفيديوهات وجلب التحليلات
                  </CardDescription>
                </div>
                {getStatusBadge(connections.youtube)}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-right block font-tajawal text-zinc-300">
                  Client ID
                </Label>
                <Input
                  value={apiKeys.youtube.client_id}
                  onChange={(e) => handleInputChange('youtube', 'client_id', e.target.value)}
                  className="bg-zinc-800/50 border-zinc-700 text-white text-right font-mono text-sm"
                  placeholder="1234567890-xxxxx.apps.googleusercontent.com"
                  data-testid="youtube-client-id-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-right block font-tajawal text-zinc-300">
                  Client Secret
                </Label>
                <Input
                  type="password"
                  value={apiKeys.youtube.client_secret}
                  onChange={(e) => handleInputChange('youtube', 'client_secret', e.target.value)}
                  className="bg-zinc-800/50 border-zinc-700 text-white text-right font-mono"
                  placeholder="GOCSPX-..."
                  data-testid="youtube-client-secret-input"
                />
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={() => handleSave('youtube')}
                  disabled={loading.youtube}
                  className="flex-1 bg-orange-500 hover:bg-orange-600 font-cairo"
                  data-testid="youtube-save-button"
                >
                  {loading.youtube ? 'جاري الحفظ...' : 'حفظ'}
                </Button>
                <Button
                  onClick={() => handleTestConnection('youtube')}
                  disabled={loading.youtube_test}
                  variant="outline"
                  className="flex-1 border-zinc-700 text-white hover:bg-zinc-800 font-cairo"
                  data-testid="youtube-test-button"
                >
                  {loading.youtube_test ? 'جاري الاختبار...' : 'اختبار الاتصال'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="google" className="space-y-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-xl font-cairo font-bold text-white flex items-center">
                <Database className="ml-2 h-5 w-5 text-orange-500" />
                Google Drive API
              </CardTitle>
              <CardDescription className="text-zinc-400 font-tajawal">
                لحفظ الفيديوهات المنشأة
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-right block font-tajawal text-zinc-300">
                  Credentials JSON
                </Label>
                <textarea
                  value={apiKeys.google_drive.credentials_json}
                  onChange={(e) => handleInputChange('google_drive', 'credentials_json', e.target.value)}
                  className="w-full min-h-[120px] bg-zinc-800/50 border border-zinc-700 rounded-lg p-3 text-white text-right font-mono text-sm"
                  placeholder='{"type": "service_account", ...}'
                  data-testid="drive-credentials-input"
                />
              </div>
              <Button
                onClick={() => handleSave('google_drive')}
                disabled={loading.google_drive}
                className="w-full bg-orange-500 hover:bg-orange-600 font-cairo"
                data-testid="drive-save-button"
              >
                {loading.google_drive ? 'جاري الحفظ...' : 'حفظ'}
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-xl font-cairo font-bold text-white flex items-center">
                <Table className="ml-2 h-5 w-5 text-orange-500" />
                Google Sheets API
              </CardTitle>
              <CardDescription className="text-zinc-400 font-tajawal">
                لتسجيل الفيديوهات المنشورة
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-right block font-tajawal text-zinc-300">
                  Sheet ID
                </Label>
                <Input
                  value={apiKeys.google_sheets.sheet_id}
                  onChange={(e) => handleInputChange('google_sheets', 'sheet_id', e.target.value)}
                  className="bg-zinc-800/50 border-zinc-700 text-white text-right font-mono"
                  placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                  data-testid="sheets-id-input"
                />
              </div>
              <Button
                onClick={() => handleSave('google_sheets')}
                disabled={loading.google_sheets}
                className="w-full bg-orange-500 hover:bg-orange-600 font-cairo"
                data-testid="sheets-save-button"
              >
                {loading.google_sheets ? 'جاري الحفظ...' : 'حفظ'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
