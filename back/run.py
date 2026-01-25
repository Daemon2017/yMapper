import json
from itertools import chain

import pandas as pd
from flask import Flask, request, Response
from flask_cors import CORS
from waitress import serve

import db

app = Flask(__name__)
cors = CORS(app)
pool = db.get_session_pool()
db.warm_up()


@app.route('/list', methods=['GET'])
def get_list():
    prefix = request.args.get('prefix')
    if not prefix:
        return Response(json.dumps({"error": "Missing parameters"}), status=400, mimetype='application/json')
    if len(prefix) < 3:
        return Response(json.dumps({"error": "Prefix length must be >=3"}), status=400, mimetype='application/json')
    print(f'Processing GET /list for prefix={prefix}...')
    response = db.select_list(prefix)
    if not response:
        return Response(json.dumps({"error": "No SNP in DB"}), status=404, mimetype='application/json')
    return Response(json.dumps(response), mimetype='application/json')


@app.route('/parent', methods=['GET'])
def get_parent():
    snp = request.args.get('snp')
    if not snp:
        return Response(json.dumps({"error": "Missing parameters"}), status=400, mimetype='application/json')
    print(f'Processing GET /parent for snp={snp}...')
    response = db.select_parent(snp)
    if not response:
        return Response(json.dumps({"error": "No SNP in DB"}), status=404, mimetype='application/json')
    return Response(json.dumps(response), mimetype='application/json')


@app.route('/centroids', methods=['GET'])
def get_centroids():
    snp = request.args.get('snp')
    size = request.args.get('size')
    group = request.args.get('group', 'false').lower() == 'true'
    if not snp or not size:
        return Response(json.dumps({"error": "Missing parameters"}), status=400, mimetype='application/json')
    print(f'Processing GET /centroids for snp={snp} and size={size}...')
    response = db.select_centroids(snp, size)
    if not response:
        return Response(json.dumps({"error": "No SNP in DB"}), status=404, mimetype='application/json')
    df = pd.DataFrame.from_records(response)
    df = df.explode('centroids').rename(columns={'centroids': 'centroid'})
    df['centroid'] = df['centroid'].map(tuple)
    df = df.groupby('centroid')['snp'].unique().reset_index().rename(columns={'snp': 'snps'})
    df['snps'] = df['snps'].map(lambda x: frozenset(x))
    df = df.groupby('snps')['centroid'].agg(list).reset_index().rename(columns={'centroid': 'centroids'})
    df['level'] = df['snps'].map(len)
    df = df.sort_values(by='level', ascending=False)
    if group:
        df = df.drop(columns=['snps'])
        df = df.groupby('level')['centroids'].apply(lambda x: list(chain.from_iterable(x))).reset_index()
        return Response(df.to_json(orient='records'), mimetype='application/json')
    else:
        df = df.drop(columns=['level'])
        return Response(df.to_json(orient='records'), mimetype='application/json')


if __name__ == '__main__':
    print('yMapper ready!')
    try:
        serve(app,
              host='0.0.0.0',
              port=8080)
    except (KeyboardInterrupt, SystemExit):
        print("Stopping yMapper...")
    finally:
        print("Closing YDB resources...")
        db.stop_pool()
        print('yMapper stopped.')
