from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagAndItemSchema

tag_blueprint = Blueprint("Tags", __name__, description="Operations on tags")

@tag_blueprint.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):
    @tag_blueprint.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)

        return store.tags.all()

    @tag_blueprint.arguments(TagSchema)
    @tag_blueprint.response(201, TagSchema)
    def post(self, tag_data, store_id):
        tag = TagModel(**tag_data, store_id=store_id)

        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))

        return tag
    
@tag_blueprint.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @tag_blueprint.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        item.tags.append(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting a tag.")

        return tag
    
    @tag_blueprint.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        item.tags.remove(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while removing a tag.")

        return {"message": "Item removed from tag", "item": item, "tag": tag}
    
@tag_blueprint.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @tag_blueprint.response(200, TagSchema())
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag
    
    @tag_blueprint.response(
        202, 
        description="Deletes a tag if no item is tagged with it.",
        example={"message": "Tag deleted."}
    )
    @tag_blueprint.alt_response(404, "Could not delete tag. Make sure tag is not associated with any items, then try again.")
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        if not tag.items:
            db.session.add(tag)
            db.session.commit()
            return {"message": "Tag deleted."}
        abort(400, message="Could not delete tag. Make sure tag is not associated with any items, then try again.")