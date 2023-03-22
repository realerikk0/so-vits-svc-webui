# -*- coding: utf-8 -*-
import tornado.web


# noinspection PyAbstractClass
class MainHandler(tornado.web.StaticFileHandler):
    """为了使用Vue Router的history模式，把不存在的文件请求转发到index.html"""
    async def get(self, path, include_body=True):
        try:
            await super().get(path, include_body)
        except tornado.web.HTTPError as e:
            if e.status_code != 404:
                raise
            # 不存在的文件请求转发到index.html，交给前段路由
            await super().get('index.html', include_body)
