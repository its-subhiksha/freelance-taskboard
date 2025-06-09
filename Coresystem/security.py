from Accounts.models import CustomUser
from django.utils import timezone
from Coresystem.models import AuthTokens
import random
import string
from celery import shared_task
import re,os,subprocess
import pandas as pd
from django.conf import settings
import socket


class AuthtokenGenerator:
    def __init__(self, token_type, user_id=None):
        self.user_id = user_id
        self.token_type = token_type
        self.token = self._generate_token()

    def _generate_token(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=64))

    def get_token(self):
        return self.token

    def get_token_expiry_time(self):
        token_choice = {1: 2, 2: 3, 3: 5, 4: 10}
        if self.token_type == 1:
            return timezone.now() + timezone.timedelta(days=token_choice[self.token_type])
        else:
            return timezone.now() + timezone.timedelta(minutes=token_choice[self.token_type])

    def issue_new_token(self):
        """Create and return a new token row in DB"""
        user = None
        try:
            if self.user_id:
                user = CustomUser.objects.get(id=self.user_id)
        except CustomUser.DoesNotExist:
            user = None

        auth_token = AuthTokens.objects.create(
            user=user,
            token=self.token,
            auth_type=self.token_type,
            is_valid=True,
            expires_on=self.get_token_expiry_time()
        )
        return auth_token.token

    def update_existing_token(self, auth_token_obj):
        """Update an existing token object with new token & expiry"""
        auth_token_obj.token = self.token
        auth_token_obj.expires_on = self.get_token_expiry_time()
        auth_token_obj.is_valid = True
        auth_token_obj.save()
        return auth_token_obj.token

def AuthTokenValidator(token,expected_type):
    try:
        token_obj = AuthTokens.objects.get(token=token, auth_type=expected_type)
        print("Token object: ", token_obj)

    except AuthTokens.DoesNotExist:
        print("Token does not exist")
        return None
    
    if not token_obj.is_valid_token() or token_obj.auth_type != expected_type:
        print("Token is not valid")
        return None
    
    print("Token validity:", token_obj.is_valid_token())
    print("Token status:", token_obj.auth_type, token_obj.token)
    
    return token_obj

@shared_task
def is_valid_email(email):
    print("comes under validating the email")
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email) is None:
        return False
    email_domain = email[(str(email).rfind("@") + 1) :].lower()
    print("Email Domainnnnnnnn: ", email_domain)
    return isnt_temp_domain(email_domain) and is_ping_valid(email_domain)


# Child functions
def isnt_temp_domain(domain):
    print("comes underr cheking the domain")
    start_time = timezone.now()
    indexes = {'0': [0, 545], '1': [546, 1412], '2': [1413, 2321], '3': [2322, 3113], '4': [3114, 3696], '5': [3697, 4264], '6': [4265, 4946], 
           '7': [4947, 5523], '8': [5524, 6291], '9': [6292, 6922], 'a': [6923, 11678], 'b': [11679, 16827], 'c': [16828, 21682], 
           'd': [21683, 25705], 'e': [25706, 28669], 'f': [28670, 31837], 'g': [31838, 35048], 'h': [35049, 38252], 'i': [38253, 40881], 
           'j': [40882, 42509], 'k': [42510, 44828], 'l': [44829, 48033], 'm': [48034, 53534], 'n': [53535, 56163], 'o': [56164, 58233], 
           'p': [58234, 62590], 'q': [62591, 63495], 'r': [63496, 66917], 's': [66918, 73501], 't': [73502, 78759], 'u': [78760, 80172], 
           'v': [80173, 82322], 'w': [82323, 84851], 'x': [84852, 86798], 'y': [86799, 88082], 'z': [88083, 89259]}

    file_data = pd.read_csv(getattr(settings, "INVALID_DOMAIN_CSV"))
    temp_domain = file_data["emaildomain"].tolist()
    start, end = indexes[domain[0]]

    while start < end:
        mid = int(len(temp_domain[start:end]) / 2)
        if domain < temp_domain[start:end][mid]:
            end = temp_domain.index(temp_domain[start:end][mid])
        elif domain > temp_domain[start:end][mid]:
            start = temp_domain.index(temp_domain[start:end][mid])
        elif domain == temp_domain[start:end][mid]:
            return False
        if mid == 0:
            return True

# def is_ping_valid(domain):
#     print("comes under ping")
#     subprocess_method = '-n' if os.getenv('OSX')=='WIN' else '-c'
#     return subprocess.call(['ping', subprocess_method, '1', domain]) == 0

def is_ping_valid(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False