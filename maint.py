# -*- coding: utf-8 -*-
import argparse
import logging
import logging.handlers
import os
import tornado.ioloop
import tornado.web
import config
import api.main
import api.svc
import api.tool
import api.vm

logger = logging.getLogger(__name__)

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
WEB_ROOT = os.path.join(BASE_PATH, 'frontend', 'dist')
LOG_FILE_NAME = os.path.join(BASE_PATH, 'log', 'sovits-webui.log')

routes = [
    (r'/api/svc/model', api.svc.ModelListHandler),
    (r'/api/svc/switch', api.svc.SwitchHandler),
    (r'/api/svc/run', api.svc.SingleInferenceHandler),
    (r'/api/svc/batch', api.svc.BatchInferenceHandler),

    (r'/api/vm/run', api.vm.VocalRemoverHandler),

    (r'/api/tool/norm', api.tool.AudioNormalizerHandler),

    (r'/(.*)', api.main.MainHandler, {'path': WEB_ROOT, 'default_filename': 'index.html'})
]


def main():
    args = parse_args()

    init_logging(args.debug)
    config.init()
    api.svc.init()

    run_server(args.host, args.port, args.debug)


def parse_args():
    parser = argparse.ArgumentParser(description="SOVITS WEBUI")
    parser.add_argument('--host', help='Server host, default to 127.0.0.1', default='127.0.0.1')
    parser.add_argument('--port', help='Server port, default to 7870', type=int, default=7870)
    parser.add_argument('--debug', help='debug mode', action='store_true')
    return parser.parse_args()


def init_logging(debug):
    stream_handler = logging.StreamHandler()
    file_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_FILE_NAME, encoding='utf-8', when='midnight', backupCount=7, delay=True
    )
    # noinspection PyArgumentList
    logging.basicConfig(
        format='{asctime} {levelname} [{name}]: {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{',
        level=logging.INFO if not debug else logging.DEBUG,
        handlers=[stream_handler, file_handler]
    )

    # 屏蔽访问日志
    logging.getLogger('tornado.access').setLevel(logging.WARNING)


def run_server(host, port, debug):
    app = tornado.web.Application(
        routes,
        websocket_ping_interval=10,
        debug=debug,
        autoreload=True
    )
    cfg = config.get_config()
    try:
        app.listen(
            port=port,
            address=host,
            xheaders=cfg.tornado_xheaders
        )
    except OSError:
        logger.warning('Address is used %s:%d', host, port)
        return
    # finally:
    #     url = f'http://{host}/' if port == 80 else f'http://{host}:{port}/'
    #     # 防止更新版本后浏览器加载缓存
    #     url += '?_v=' + update.VERSION
    #     webbrowser.open(url)
    logger.info('Server started: %s:%d', host, port)
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.current().instance().stop()


if __name__ == '__main__':
    main()
