#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""API скоринга"""

import datetime
import hashlib
import json
import logging
import uuid
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer

import src.otus_hw5.scoring as scoring
from src.otus_hw5.store import ScoringStore

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class FieldRequired(object):
    """Базовый класс - валидатор с атрибутом Required."""

    def __init__(self, required: bool):
        self.required = required
        self.value = ""

    def __get__(self, instance, owner):
        return self.value


class FieldValidator(FieldRequired):
    """Базовый класс - валидатор с атрибутами Required и Nullable."""

    def __init__(self, required: bool, nullable: bool):
        super().__init__(required=required)
        self.nullable = nullable


class CharField(FieldValidator):
    """Валидатор символьного поля."""

    def __set__(self, instance, value):
        if value is None:
            self.value = None
        elif isinstance(value, str):
            self.value = value
        else:
            raise ValueError("Invalid char value")


class ArgumentsField(FieldValidator):
    """Валидатор словаря аргументов."""

    def __init__(self, required: bool, nullable: bool):
        super().__init__(required, nullable)
        self.value = {}

    def __set__(self, instance, value):
        if value is None:
            self.value = None
        elif isinstance(value, dict):
            self.value = value
        else:
            raise ValueError("Invalid arguments value")


class EmailField(CharField):
    """Валидатор адреса электронной почты."""

    def __set__(self, instance, value):
        old_value = self.value
        super().__set__(instance, value)
        if value is None:
            self.value = None
        elif value.find("@") > 0 and not value.endswith("@"):
            self.value = value
        else:
            self.value = old_value
            raise ValueError("Invalid email address")


class PhoneField(FieldValidator):
    """Валидатор номера телефона."""

    def __set__(self, instance, value):
        if value is None:
            self.value = None
        elif isinstance(value, str) and value.startswith("7") and len(value) == 11:
            self.value = value
        elif isinstance(value, int) and 70000000000 <= value <= 79999999999:
            self.value = str(value)
        else:
            raise ValueError("Invalid phone number")


class DateField(FieldValidator):
    """Валидатор даты."""

    def __init__(self, required: bool, nullable: bool):
        super().__init__(required, nullable)
        self.value = datetime.date(year=datetime.MINYEAR, month=1, day=1)

    def __set__(self, instance, value):
        if value is None:
            self.value = None
        elif isinstance(value, str) and len(value) == 10:
            self.value = datetime.datetime.strptime(value, "%d.%m.%Y").date()
        else:
            raise ValueError("Invalid date")


class BirthDayField(DateField):
    """Валидатор даты рождения."""

    def __set__(self, instance, value):
        old_value = self.value
        super().__set__(instance, value)
        years0 = datetime.timedelta()
        years70 = datetime.timedelta(days=365) * 70

        if value is None:
            self.value = None
        elif not years0 <= datetime.date.today() - self.value <= years70:
            self.value = old_value
            raise ValueError("Invalid birthday")


class GenderField(FieldValidator):
    """Валидатор пола."""

    def __set__(self, instance, value):
        if value is None:
            self.value = None
        elif value in GENDERS.keys():
            self.value = value
        else:
            raise ValueError("Invalid gender")


class ClientIDsField(FieldRequired):
    """Валидатор списка клиентов."""

    def __init__(self, required: bool):
        super().__init__(required)
        self.value = []

    def __set__(self, instance, value):
        if value is None:
            self.value = None
        elif isinstance(value, list) and all(isinstance(i, int) for i in value):
            self.value = value
        else:
            raise ValueError("ClientIDs is not a list")


class MetaRequest(type):
    """Метакласс для создания Request-классов."""

    def create_local_attrs(self, *args, **kwargs):
        """Замена стандартного инициализатора Request-классов."""

        for key, value in self.class_attrs.items():
            # Если атрибут обязательный, но не передан или None,
            # вызываем исключение
            if self.class_attrs[key].required and (
                key not in kwargs or kwargs[key] is None
            ):
                raise ValueError(f"Mandatory attribute {key} is not set")
            # Если атрибут не должен быть пустым, но пуст (длина 0),
            # вызываем исключение
            if (
                not hasattr(self.class_attrs[key], "nullable")
                or not self.class_attrs[key].nullable
            ) and len(kwargs.get(key, "")) == 0:
                raise ValueError(f"Attribute {key} is not nullable")
            # Если атрибут передан
            if key in kwargs:
                # Добавляем атрибут уровня экземпляра
                setattr(self, key, kwargs[key])

    def __init__(cls, name, bases, attrs):
        """Инициализатор."""

        super().__init__(name, bases, attrs)
        # Сохраняем атрибуты класса в словаре
        # Исключаем magic-атрибуты, свойства и методы
        cls.class_attrs = {
            k: v
            for k, v in attrs.items()
            if not k.startswith("__")
            and not isinstance(v, property)
            and not callable(v)
        }
        # Подменяем инициализатор Request-классов
        cls.__init__ = MetaRequest.create_local_attrs


class ClientsInterestsRequest(metaclass=MetaRequest):
    """Атрибуты интересов."""

    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(metaclass=MetaRequest):
    """Атрибуты для скоринга."""

    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


class MethodRequest(metaclass=MetaRequest):
    """Запрос к API."""

    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        """Проверка, является ли пользователь админом."""
        return self.login == ADMIN_LOGIN


def check_auth(request):
    """Аутентификация."""

    if request.is_admin:
        digest = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode("utf-8")
        ).hexdigest()
    else:
        digest = hashlib.sha512(
            (request.account + request.login + SALT).encode("utf-8")
        ).hexdigest()
    return digest == request.token


def online_score_request(request: MethodRequest, ctx, store:ScoringStore):
    """Запрос скоринга."""

    response, code = None, None

    if request.is_admin:
        # Режим администратора
        score = 42
    elif len(request.arguments) == 0:
        # Пустой список аргументов
        code = INVALID_REQUEST
        response = {"error": "Empty arguments list"}
        return response, code
    else:
        # Парсинг списка аргументов с валидацией
        arguments = OnlineScoreRequest(
            first_name=request.arguments.get("first_name"),
            last_name=request.arguments.get("last_name"),
            email=request.arguments.get("email"),
            phone=request.arguments.get("phone"),
            birthday=request.arguments.get("birthday"),
            gender=request.arguments.get("gender"),
        )

        # Проверка на обязательные пары аргументов
        if (
            (arguments.phone is None or arguments.email is None)
            and (arguments.first_name is None or arguments.last_name is None)
            and (arguments.gender is None or arguments.birthday is None)
        ):
            code = INVALID_REQUEST
            response = {"error": "Incomplete arguments list"}
            return response, code

        # Получение скоринга
        score = scoring.get_score(
            store=store,
            phone=arguments.phone,
            email=arguments.email,
            birthday=arguments.birthday,
            gender=arguments.gender,
            first_name=arguments.first_name,
            last_name=arguments.last_name,
        )

    # Сохраняем в контексте количество переданных аргументов
    ctx["has"] = [arg for arg, _ in request.arguments.items()]

    code = OK
    response = {"score": score}
    return response, code


def clients_interest_request(request: MethodRequest, ctx, store:ScoringStore):
    """Запрос интересов."""

    response, code = None, None

    # Парсинг списка аргументов с валидацией
    arguments = ClientsInterestsRequest(
        client_ids=request.arguments.get("client_ids"),
        date=request.arguments.get("date"),
    )

    code = OK
    response = {}

    # Выбираем интересы каждого клиента. Результат Dict[int,List]
    for id in arguments.client_ids:
        response[id] = scoring.get_interests(store=store, cid=id)

    # Сохраняем в контексте количество клиентов
    ctx["nclients"] = len(arguments.client_ids)

    return response, code


def method_request(body, ctx, store:ScoringStore):
    """Запрос к API."""

    response, code = None, None

    # Парсинг запроса с валидацией
    method_req = MethodRequest(
        account=body.get("account"),
        login=body.get("login"),
        token=body.get("token"),
        arguments=body.get("arguments"),
        method=body.get("method"),
    )
    # Аутентификация
    if not check_auth(method_req):
        code = FORBIDDEN
        response = {"error": "Invalid token"}
    # Запрос скоринга
    elif method_req.method == "online_score":
        response, code = online_score_request(request=method_req, ctx=ctx,
                                              store=store)
    # Запрос увлечений
    elif method_req.method == "clients_interests":
        response, code = clients_interest_request(request=method_req, ctx=ctx,
                                                  store=store)
    # Неизвестный запрос
    else:
        code = INVALID_REQUEST
        response = {"error": "Invalid method"}

    return response, code


def method_handler(request, ctx, store:ScoringStore):
    """Обработчик обращения к API."""

    response, code = None, None

    # Ошибка - пустое тело запроса
    if len(request) == 0 or len(request.get("body")) == 0:
        code = INVALID_REQUEST
        response = {"error": "Empty request"}
    else:
        try:
            # Парсим запрос
            response, code = method_request(request.get("body"), ctx, store)
        except ValueError as ve:
            code = INVALID_REQUEST
            response = {"error": ve}

    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}


    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.store = ScoringStore()

    @staticmethod
    def get_request_id(self, headers):
        return headers.get("HTTP_X_REQUEST_ID", uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(data_string)
        except BaseException:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers},
                        context,
                        self.store,
                    )
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {
                "error": response or ERRORS.get(code, "Unknown Error"),
                "code": code,
            }
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode("utf-8"))
        return


if __name__ == "__main__":
    # k = ClientsInterestsRequest(client_ids="4",date="2025-03-09")
    # k.client_ids = "5"
    # print(k.__dict__)
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
