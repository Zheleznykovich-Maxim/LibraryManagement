import os

import httpx
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer

BOOK_SERVICE_HOST_URL = 'http://localhost:8003/api/v1/books/'

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_authorization_header(token: str):
    return {"Authorization": f"Bearer {token}"}


async def is_book_present(book_id: int, token: str = Depends(oauth2_scheme)):
    url = os.environ.get('BOOK_SERVICE_HOST_URL') or BOOK_SERVICE_HOST_URL

    headers = get_authorization_header(token)

    async with httpx.AsyncClient() as client:
        r = await client.get(f'{url}{book_id}', headers=headers)

    return True if r.status_code == 200 else False
