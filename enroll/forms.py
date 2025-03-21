from django import forms
from .models import AuthLogin



class AuthLoginForm(forms.ModelForm):
    class Meta:
        model = AuthLogin
        fields = ['fullname', 'email', 'contact', 'age', 'city', 'state', 'profile_pic']
        widgets = {
            'password': forms.PasswordInput(),
        }



class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label="Your email")



class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, label="Enter the OTP")



class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")



class ProfileForm(forms.Form):
    email = forms.EmailField()
    # phone = forms.CharField(max_length=15)
    # address = forms.CharField(widget=forms.Textarea)






