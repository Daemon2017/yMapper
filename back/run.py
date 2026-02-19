from flask import Flask, request, jsonify
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
        return jsonify([]), 200
    return jsonify(response)


@app.route('/parent', methods=['GET'])
def get_parent():
    snp = request.args.get('snp')
    if not snp:
        return jsonify({"error": "Missing parameters"}), 400
    print(f'Processing GET /parent for snp={snp}...')
    response = db.select_parent(snp)
    if not response:
        return jsonify([]), 200
    return jsonify(response)


@app.route('/centroids/dispersion', methods=['GET'])
def get_centroids_dispersion():
    snp = request.args.get('snp')
    size = request.args.get('size')
    group = request.args.get('group', 'false').lower() == 'true'
    if not all([snp, size]):
        return jsonify({"error": "Missing parameters"}), 400
    print(f'Processing GET /centroids/dispersion for snp={snp} and size={size} and group={group}...')
    response = db.select_centroids_dispersion(snp, size)
    if not response:
        return jsonify([]), 200
    return jsonify(utils.process_centroids(response, group))


@app.route('/centroids/homeland', methods=['GET'])
def get_centroids_homeland():
    snp = request.args.get('snp')
    size = request.args.get('size')
    if not all([snp, size]):
        return jsonify({"error": "Missing parameters"}), 400
    print(f'Processing GET /centroids/homeland for snp={snp} and size={size}...')
    response = db.select_homeland(snp, size)
    if not response:
        return jsonify([]), 200
    return jsonify(utils.calculate_homeland(response))


@app.route('/centroids/union', methods=['POST'])
def get_centroids_union():
    body = request.get_json()
    args = request.args
    a_points, b_points, start, end, group, size = utils.get_input(args, body)
    if not all([a_points, size, start, end]):
        return jsonify({"error": "Missing parameters"}), 400
    print(
        f'Processing POST /centroids/union for a_points={a_points} and b_points={b_points} and size={size} and start={start} and end={end} and group={group}...')
    response = db.select_centroids_union(a_points, b_points, size, start, end)
    if not response:
        return jsonify([]), 200
    return jsonify(utils.process_centroids(response, group))


@app.route('/centroids/subtraction', methods=['POST'])
def get_centroids_subtraction():
    body = request.get_json()
    args = request.args
    a_points, b_points, start, end, group, size = utils.get_input(args, body)
    if not all([a_points, b_points, size, start, end]):
        return jsonify({"error": "Missing parameters"}), 400
    print(
        f'Processing POST /centroids/subtraction for a_points={a_points} and b_points={b_points} and size={size} and start={start} and end={end} and group={group}...')
    response = db.select_centroids_subtraction(a_points, b_points, size, start, end)
    if not response:
        return jsonify([]), 200
    return jsonify(utils.process_centroids(response, group))


@app.route('/centroids/intersection', methods=['POST'])
def get_centroids_intersection():
    body = request.get_json()
    args = request.args
    a_points, b_points, start, end, group, size = utils.get_input(args, body)
    if not all([a_points, b_points, size, start, end]):
        return jsonify({"error": "Missing parameters"}), 400
    print(
        f'Processing POST /centroids/intersection for a_points={a_points} and b_points={b_points} and size={size} and start={start} and end={end} and group={group}...')
    response = db.select_centroids_intersection(a_points, b_points, size, start, end)
    if not response:
        return jsonify([]), 200
    return jsonify(utils.process_centroids(response, group))


@app.route('/centroids/xor', methods=['POST'])
def get_centroids_xor():
    body = request.get_json()
    args = request.args
    a_points, b_points, start, end, group, size = utils.get_input(args, body)
    if not all([a_points, b_points, size, start, end]):
        return jsonify({"error": "Missing parameters"}), 400
    print(
        f'Processing POST /centroids/xor for a_points={a_points} and b_points={b_points} and size={size} and start={start} and end={end} and group={group}...')
    response = db.select_centroids_xor(a_points, b_points, size, start, end)
    if not response:
        return jsonify([]), 200
    return jsonify(utils.process_centroids(response, group))


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
