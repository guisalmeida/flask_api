from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    jwt_required,
    create_refresh_token,
    get_jwt_identity
)

from db import db
from models import UserModel
from schemas import UserSchema
from blocklist import BLOCKLIST

user_blueprint = Blueprint("Users", __name__, description="Operations on users")

@user_blueprint.route("/register")
class UserRegister(MethodView):
    @user_blueprint.arguments(UserSchema)
    def post(self, user_data):
        # if UserModel.query.filter(UserModel.username == user_data["username"]).first():
        #     abort(409, message="A user with that username already exists.")

        user = UserModel(
            username=user_data["username"],
            password=pbkdf2_sha256.hash(user_data["password"]),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError as e:
            abort(500, message=str(e))

        return {"message": "User created successfully."}, 201


@user_blueprint.route("/login")
class UserLogin(MethodView):
    @user_blueprint.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

        abort(401, message="Invalid credentials.")


@user_blueprint.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}, 200
    

@user_blueprint.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        # Make it clear that when to add the refresh token to the blocklist will depend on the app design
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token": new_token}, 200


@user_blueprint.route("/user/<int:user_id>")
class User(MethodView):
    """
    This resource can be useful when testing our Flask app.
    We may not want to expose it to public users, but for the
    sake of demonstration in this course, it can be useful
    when we are manipulating data regarding the users.
    """

    @user_blueprint.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted."}, 200