import React, { useState } from 'react';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle 
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Lock, AlertTriangle } from 'lucide-react';

const PasswordChangeDialog = ({ open, onClose, onSuccess, required = false }) => {
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.new_password !== formData.confirm_password) {
      setError('새 비밀번호가 일치하지 않습니다.');
      setLoading(false);
      return;
    }

    if (formData.new_password.length < 6) {
      setError('비밀번호는 최소 6자 이상이어야 합니다.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        onSuccess(data.message);
        setFormData({
          current_password: '',
          new_password: '',
          confirm_password: ''
        });
        onClose();
      } else {
        setError(data.error || '비밀번호 변경에 실패했습니다.');
      }
    } catch (error) {
      setError('서버 연결에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={required ? undefined : onClose}>
      <DialogContent className="sm:max-w-[425px]" hideCloseButton={required}>
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Lock className="h-5 w-5" />
            <span>비밀번호 변경</span>
          </DialogTitle>
          <DialogDescription>
            {required ? (
              <div className="flex items-center space-x-2 text-amber-600">
                <AlertTriangle className="h-4 w-4" />
                <span>보안을 위해 비밀번호를 변경해주세요.</span>
              </div>
            ) : (
              '새로운 비밀번호를 설정하세요.'
            )}
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current_password">현재 비밀번호</Label>
            <Input
              id="current_password"
              name="current_password"
              type="password"
              placeholder="현재 비밀번호를 입력하세요"
              value={formData.current_password}
              onChange={handleChange}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="new_password">새 비밀번호</Label>
            <Input
              id="new_password"
              name="new_password"
              type="password"
              placeholder="새 비밀번호를 입력하세요 (최소 6자)"
              value={formData.new_password}
              onChange={handleChange}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm_password">새 비밀번호 확인</Label>
            <Input
              id="confirm_password"
              name="confirm_password"
              type="password"
              placeholder="새 비밀번호를 다시 입력하세요"
              value={formData.confirm_password}
              onChange={handleChange}
              required
            />
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex justify-end space-x-2">
            {!required && (
              <Button type="button" variant="outline" onClick={onClose}>
                취소
              </Button>
            )}
            <Button type="submit" disabled={loading}>
              {loading ? '변경 중...' : '비밀번호 변경'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default PasswordChangeDialog;

