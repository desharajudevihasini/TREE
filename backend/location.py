"""Optional, consent-based browser geolocation to UK postcode; no coordinate storage.

GPS can locate a nearby *postcode*, NOT establish the exact home or EPC record.
Uses the public postcodes.io reverse postcode endpoint; sends coordinates to
that third party only after the user presses the permission button.
"""
from __future__ import annotations
import httpx


def postcode_near_coordinates(latitude: float, longitude: float) -> dict:
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError('Invalid geographic coordinates.')
    if not (49 <= latitude <= 61.5 and -9 <= longitude <= 2.5):
        return {'status': 'outside_uk', 'postcode': None,
                'message': 'This demo supports UK EPC records. Please enter a UK postcode or use manual entry.'}
    try:
        # Reverse postcode is approximate; user MUST check the returned code.
        response = httpx.get('https://api.postcodes.io/postcodes',
                             params={'lat': latitude, 'lon': longitude, 'limit': 1, 'radius': 500},
                             timeout=5.0)
        response.raise_for_status()
        records = response.json().get('result') or []
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return {'status': 'lookup_unavailable', 'postcode': None,
                'message': 'Could not reverse-locate a postcode. Please type it manually.'}
    postcode = records[0].get('postcode') if records else None
    return {'status': 'approximate_postcode' if postcode else 'not_found', 'postcode': postcode,
            'message': ('Nearby postcode found. Check it carefully; GPS does NOT identify your house.'
                        if postcode else 'No nearby UK postcode found. Enter one manually.'),
            'privacy': 'Coordinates were sent once to postcodes.io for this lookup and are not retained by TREE.'}
