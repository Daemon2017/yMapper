import json

import pandas as pd
from flask import Flask, request, Response
from flask_cors import CORS
from waitress import serve

import db
import utils

app = Flask(__name__)
cors = CORS(app)


@app.route('/list', methods=['GET'])
def get_list():
    print(f'Processing GET /list...')
    response = db.select_list()
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
    print(f'Processing GET /centroids for snp={snp} and size={size} and group={group}...')
    response = db.select_centroids(snp, size)
    if not response:
        return Response(json.dumps({"error": "No SNP in DB"}), status=404, mimetype='application/json')
    df = pd.DataFrame.from_records(response)
    df = df.explode('centroids').rename(columns={'centroids': 'centroid'})
    df['centroid'] = df['centroid'].map(tuple)
    if group:
        df = df.groupby('centroid')['snp'].nunique().reset_index() \
            .groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'level', 'centroid': 'centroids'}) \
            .sort_values(by='level', ascending=False)
    else:
        df = df.groupby('centroid')['snp'].apply(lambda x: tuple(sorted(set(x)))).reset_index() \
            .groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'snps', 'centroid': 'centroids'})
        df = df.assign(snps_len=df['snps'].str.len()) \
            .sort_values(by='snps_len', ascending=False) \
            .drop(columns=['snps_len'])
    return Response(df.to_json(orient='records'), mimetype='application/json')


@app.route('/centroids2', methods=['GET'])
def get_centroids2():
    points = json.loads(request.args.get('points'))
    size = request.args.get('size')
    start = request.args.get('start')
    end = request.args.get('end')
    group = request.args.get('group', 'false').lower() == 'true'
    if not points or not size or not start or not end:
        return Response(json.dumps({"error": "Missing parameters"}), status=400, mimetype='application/json')
    print(
        f'Processing GET /centroids2 for points={points} and size={size} and start={start} and end={end} and group={group}...')
    response = db.select_centroids2(points, size, start, end)
    df = pd.DataFrame.from_records(response)
    df = df.explode('centroids').rename(columns={'centroids': 'centroid'})
    df['centroid'] = df['centroid'].map(tuple)
    if group:
        df = df.groupby('centroid')['snp'].nunique().reset_index() \
            .groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'level', 'centroid': 'centroids'}) \
            .sort_values(by='level', ascending=False)
    else:
        df = df.groupby('centroid')['snp'].apply(lambda x: tuple(sorted(set(x)))).reset_index() \
            .groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'snps', 'centroid': 'centroids'})
        df = df.assign(snps_len=df['snps'].str.len()) \
            .sort_values(by='snps_len', ascending=False) \
            .drop(columns=['snps_len'])
    return Response(df.head(50).to_json(orient='records'), mimetype='application/json')


@app.route('/hexagon', methods=['GET'])
def get_hexagon():
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    size = float(request.args.get('size'))
    if not lat or not lng or not size:
        return Response(json.dumps({"error": "Missing parameters"}), status=400, mimetype='application/json')
    print(f'Processing GET /hexagon for lat={lat} and lng={lng} and size={size}...')
    hexagon = utils.get_hexagon(size, -180, lng + size, lng, -90, lat + size, lat)
    centroid = hexagon.centroid
    return Response(json.dumps([round(centroid.y, 4), round(centroid.x, 4)]), mimetype='application/json')


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.Session.remove()


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
