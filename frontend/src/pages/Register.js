import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Play } from 'lucide-react';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      toast.error('كلمات المرور غير متطابقة');
      return;
    }

    setLoading(true);
    const result = await register(email, password);
    setLoading(false);
    
    if (result.success) {
      toast.success('تم إنشاء الحساب بنجاح');
      navigate('/dashboard');
    } else {
      toast.error(result.error);
    }
  };

  return (
    <div dir="rtl" className="min-h-screen bg-[#09090b] flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500/20 to-orange-600/10 border border-orange-500/30 mb-4">
            <Play className="w-8 h-8 text-orange-500" fill="currentColor" />
          </div>
          <h1 className="text-4xl font-cairo font-bold text-white mb-2">يو.آي</h1>
          <p className="text-zinc-400 font-tajawal">منصة أتمتة يوتيوب بالذكاء الاصطناعي</p>
        </div>

        <div className="bg-[#121214] border border-zinc-800 rounded-2xl p-8 shadow-xl">
          <h2 className="text-2xl font-cairo font-bold text-white mb-6 text-right">إنشاء حساب جديد</h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-right block font-tajawal text-zinc-300">
                البريد الإلكتروني
              </Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-zinc-900/50 border-zinc-800 text-white text-right font-tajawal"
                placeholder="ادخل بريدك الإلكتروني"
                required
                data-testid="register-email-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-right block font-tajawal text-zinc-300">
                كلمة المرور
              </Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-zinc-900/50 border-zinc-800 text-white text-right font-tajawal"
                placeholder="ادخل كلمة المرور"
                required
                data-testid="register-password-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-right block font-tajawal text-zinc-300">
                تأكيد كلمة المرور
              </Label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="bg-zinc-900/50 border-zinc-800 text-white text-right font-tajawal"
                placeholder="أعد إدخال كلمة المرور"
                required
                data-testid="register-confirm-password-input"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white font-cairo font-bold py-6 rounded-xl shadow-lg shadow-orange-500/20 transition-all duration-300 hover:shadow-orange-500/40"
              data-testid="register-submit-button"
            >
              {loading ? 'جاري إنشاء الحساب...' : 'إنشاء الحساب'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-zinc-400 font-tajawal">
              لديك حساب بالفعل؟{' '}
              <Link to="/login" className="text-orange-500 hover:text-orange-400 font-bold">
                تسجيل الدخول
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
