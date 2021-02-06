import json

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccount.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

for c in ['snps', 'snps_extended']:
    collection_ref = db.collection(c)
    collection = collection_ref.get()

    snps_list = []
    for snp in collection:
        snps_list.append(snp.id)

    doc_ref = db.collection(c).document('list')
    doc_ref.set({
        u'data': json.dumps(snps_list)
    })
