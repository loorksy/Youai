import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  ar: {
    translation: {
      dashboard: 'لوحة التحكم',
      createVideo: 'إنشاء فيديو',
      settings: 'الإعدادات',
      analytics: 'التحليلات',
      trends: 'الترندات',
      publishQueue: 'قائمة النشر',
      logout: 'تسجيل الخروج',
      login: 'تسجيل الدخول',
      register: 'إنشاء حساب',
      email: 'البريد الإلكتروني',
      password: 'كلمة المرور',
      totalVideos: 'إجمالي الفيديوهات',
      publishedVideos: 'الفيديوهات المنشورة',
      totalViews: 'إجمالي المشاهدات',
      activeCampaigns: 'الحملات النشطة',
      recentVideos: 'الفيديوهات الأخيرة',
      topic: 'الموضوع',
      videoDimensions: 'أبعاد الفيديو',
      videoLength: 'طول الفيديو',
      aiGenerator: 'منشئ الذكاء الاصطناعي',
      createNow: 'إنشاء الآن',
      status: 'الحالة',
      views: 'المشاهدات',
      likes: 'الإعجابات',
      comments: 'التعليقات',
      engagementRate: 'معدل التفاعل',
      trendingTopics: 'الموضوعات الرائجة',
      apiConnections: 'اتصالات API',
      testConnection: 'اختبار الاتصال',
      save: 'حفظ',
      cancel: 'إلغاء',
      delete: 'حذف',
      edit: 'تعديل'
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'ar',
    fallbackLng: 'ar',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
