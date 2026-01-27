from django.shortcuts import redirect

# ログイン確認
class AdministratorLoginRequiredMixin:

    def dispatch(self, request, *args, **kwargs):
        if 'login_id' not in request.session:
            # ログイン画面に飛ばす
            return redirect('administrator:login')
        return super().dispatch(request, *args, **kwargs)