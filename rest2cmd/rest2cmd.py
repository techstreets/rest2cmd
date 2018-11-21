# -*- coding: utf-8 -*-
import sys
import os
import json
import yaml
import string
import random
import shlex
import subprocess
from traceback import format_exc
from flask import Flask, request, jsonify

app = Flask(__name__)
app.url_map.strict_slashes = False

assert 'APP_ROOT' in os.environ, 'No APP_ROOT env variable found!'
APP_ROOT = os.environ['APP_ROOT']
print('APP_ROOT', APP_ROOT)

assert 'HTTP_MAP_PATH' in os.environ, 'No HTTP_MAP_PATH env variable found!'
HTTP_MAP_PATH = os.environ['HTTP_MAP_PATH']
print('HTTP_MAP_PATH', HTTP_MAP_PATH)

with open(HTTP_MAP_PATH, 'r') as f:
    try:
        HTTP_MAP = yaml.load(f)
    except yaml.YAMLError as exc:
        print('Problem loading yaml http map file', file=sys.stderr)
        print(exc, file=sys.stderr)
        sys.exit(1)

print('HTTP_MAP', HTTP_MAP, file=sys.stderr)
assert not isinstance('HTTP_MAP', dict), (
    'Wrong content in HTTP_MAP! Got %r' % HTTP_MAP
)


def execute(executable, command, plugin_path):
    try:
        cmd = '%s %s' % (executable, command)
        parts = shlex.split(cmd)
        cwd = os.path.normpath(os.path.join(APP_ROOT, plugin_path))
        print(
            'Resolved as: %s | @%s | %s' % (cmd, cwd, parts), file=sys.stderr
        )
        proc = subprocess.Popen(
            parts,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd
        )
        # wait for the process to terminate
        # while proc.poll() is None:
        #     time.sleep(0.2)
        out, err = proc.communicate()
        # wrap response
        is_error = proc.returncode != 0
        content_stream = (err if is_error else out).decode('utf8').strip()
        content = content_stream.split('\n')
        return {
            'is_error': is_error,
            'content':  content
        }
    except Exception:
        return {
            'is_error': True,
            'content': format_exc().split('\n')
        }


def format_status(output):
    if output['is_error']:
        return 400
    if len(output['content']) == 0:
        return 204
    return 200


def format_output(output, is_json):
    # if app outpput is json format, it means there is a single line
    # of output or there is empty output
    # if it's not json, simply return what is in output content
    if is_json and len(output['content']) > 0:
        # it should be single line, first one, with json content
        # try to parse it, and if it fails, failover to plain text lines
        # this could be case if output is an error, like traceback
        # and executable has no control over this and can't json it
        try:
            return json.loads(output['content'][0])
        except json.decoder.JSONDecodeError:
            pass
    return output['content']


def normalize_url_args(**url_args):
    normalized = {}
    for arg_name in url_args:
        value = url_args[arg_name]
        normalized[arg_name] = ('\'%s\'' if ' ' in value else '%s') % value
    return normalized


def route_handler(path, method, config):

    def _call(**url_args):
        data = request.json or {}
        payload = {**url_args, 'http_payload': json.dumps(data)}
        for k, v in (data if isinstance(data, dict) else {}).items():
            payload['http_payload__%s' % k] = v
        payload = normalize_url_args(**payload)
        print('Got payload: %s', payload, file=sys.stderr)
        command_parts = [p % payload for p in config['command'].split()]
        config['command'] = ' '.join(command_parts)
        print('Executing: %s', config['command'], file=sys.stderr)
        output = execute(
            config['executable'], config['command'], config['plugin_path']
        )
        print('Got output: %s', output, file=sys.stderr)
        content = format_output(output, config.get('is_json', False))
        status = format_status(output)
        print('http response(%d): %s' % (status, content), file=sys.stderr)
        return jsonify(content), status

    # id(_call) is always unique, but we need to randomize name
    _call.__name__ = ''.join(
        random.choice(string.ascii_lowercase) for _ in range(10)
    )
    app.route(path, methods=[method])(_call)


# dynamically create flask routes from http map
for method, routes in HTTP_MAP.items():
    for path, config in routes.items():
        route_handler(path, method, config)

print('Starting app ..', file=sys.stderr)

if __name__ == '__main__':
    app.run()
