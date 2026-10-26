"""Opt-in Gemini image review: suggestions only, NEVER trusted property facts or scores.

Requires a team-owned GEMINI_API_KEY plus explicit per-image consent. Not used by
any energy/score endpoint. No images are persisted by TREE.
"""
from __future__ import annotations
import base64
import os
import httpx


def review_image(data:bytes, filename:str, consent:bool) -> dict:
    if not consent:raise PermissionError('Please explicitly consent before TREE sends an image to Gemini.')
    key=os.getenv('GEMINI_API_KEY','').strip()
    if not key:raise RuntimeError('Gemini image analysis is not configured; no image was transmitted.')
    from backend.home_extras import inspect_media
    meta=inspect_media(data,filename,'')
    if meta['type']!='image':raise ValueError('Only image files can be sent for optional vision review.')
    if len(data)>4*1024*1024:raise ValueError('Image exceeds the 4 MB vision limit.')
    ext=filename.rsplit('.',1)[-1].lower()
    mime={'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','webp':'image/webp'}.get(ext)
    if not mime:raise ValueError('Unsupported vision format')
    prompt=("You are a cautious assistant inspecting a photo optionally supplied by a homeowner. "
      "State only details visible in the image that may help the user verify window glazing, heating equipment, "
      "an appliance nameplate or an energy bill. Never infer an EPC rating, insulation inside walls, "
      "annual electricity or gas use from a photo, and never calculate energy, carbon or home value. "
      "Report uncertain observations as uncertain, do not make up names, dates or numbers. "
      "Reply in 3 short bullet points, and end with: 'Homeowner verification required.'")
    model=os.getenv('GEMINI_MODEL','gemini-2.5-flash')
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    try:
        with httpx.Client(timeout=20) as client:
            response=client.post(url,params={'key':key},json={'contents':[{'parts':[
                 {'text':prompt}, {'inline_data':{'mime_type':mime,'data':base64.b64encode(data).decode('ascii')}}]}],
                 'generationConfig':{'temperature':0.0,'maxOutputTokens':350}})
            response.raise_for_status()
            message=response.json()['candidates'][0]['content']['parts'][0]['text']
    except (httpx.HTTPError,KeyError,IndexError,ValueError) as exc:
        raise RuntimeError('Gemini could not analyze the image. No candidate claims were accepted.') from exc
    return {'candidate_observations':message[:1600], 'verified':False,'used_for_calculations':False,
            'provider':'Google Gemini','requires_homeowner_confirmation':True,
            'privacy':'Explicitly sent to Gemini with consent. TREE does not store the image. Check the provider privacy terms.'}
