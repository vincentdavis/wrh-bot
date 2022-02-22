import datetime
import decimal
import inspect
import json
from urllib.parse import urlparse

import aiohttp

from wrh_bot.settings import ZWIFTPOWER_USERNAME, ZWIFTPOWER_PASSWORD, ZWIFT_POWER_LOGIN_URL


def to_dict(obj, fields=None, fields_map=None, extra_fields=None):
    """
    convert a model object to a python dict.
    @param obj: object of a db model
    @param fields: list of fields which we want to show in return value.
        if fields=None, we show all fields of model object
    @type fields: list
    @param fields_map: a map converter to show fields as a favorite.
        every field can bind to a lambda function in fields_map.
        if a field was bind to a None value in fields_map, we ignore this field
        to show in result
    @type fields_map: dict
    @param extra_fields: add new or override existing fields
    """
    data = {}
    fields_map = fields_map or {}

    if fields is None:
        fields = [f.name for f in obj.__class__._meta.fields]
    fields.extend(extra_fields or [])
    for field in fields:
        if field in fields_map:
            if fields_map[field] is None:
                continue
            func = fields_map.get(field)
            if len(inspect.signature(func).parameters) == 1:
                v = func(obj)
            else:
                v = func()
        else:
            v = getattr(obj, field, None)
        if isinstance(v, datetime.datetime):
            data[field] = v.isoformat() + 'Z'
        elif isinstance(v, datetime.date):
            data[field] = v.isoformat()
        elif isinstance(v, decimal.Decimal):
            data[field] = float(v)
        else:
            data[field] = v

    return data


async def zwift_power_get_api_async(url):
    p = urlparse(url)
    data = {}
    login_data = {
        'username': ZWIFTPOWER_USERNAME, 'password': ZWIFTPOWER_PASSWORD,
        'login': 'Login'
    }

    # this is strange! but this is required to have a user-agent header for fetching above url
    async with aiohttp.ClientSession() as session:
        async with session.get(ZWIFT_POWER_LOGIN_URL, headers={"User-Agent": "Requests Agent"}) as res:
            login_data['sid'] = res.cookies.get('phpbb3_lswlk_sid').value

        async with session.post(ZWIFT_POWER_LOGIN_URL, data=login_data, headers={"User-Agent": "Requests Agent"}) as res:
            await res.text()

        async with session.get(url, headers={"User-Agent": "Requests Agent"}) as res:
            text = await res.json()

    data = text
    return data