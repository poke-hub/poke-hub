from flask_wtf import FlaskForm
from wtforms import FileField, HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class CommunityForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=64)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=512)])
    logo = FileField("Logo (opcional)", validators=[Optional()])
    banner = FileField("Banner (opcional)", validators=[Optional()])
    submit = SubmitField("Create")


class ProposeDatasetForm(FlaskForm):
    dataset_id = HiddenField("dataset_id", validators=[DataRequired()])
    message = TextAreaField("Message (optional)", validators=[Optional(), Length(max=1024)])
    submit = SubmitField("Propose to community")


class UpdateCommunityForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=64)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=512)])
    logo = FileField("Logo (optional)")
    banner = FileField("Banner (optional)")
    submit = SubmitField("Update community")
