import pandera as pa
from pandera.typing import DataFrame, Series

class NetflixFeatureSchema(pa.DataFrameModel):
    customer_id: Series[int] = pa.Field(ge=1)
    recency_days: Series[int] = pa.Field(ge=0, le=2000)
    frequency: Series[int] = pa.Field(ge=0)
    monetary: Series[float] = pa.Field(ge=0.0, le=5.0)
    tenure_days: Series[int] = pa.Field(ge=0)
    num_products: Series[int] = pa.Field(ge=1, le=50)
    engagement_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    days_since_service: Series[int] = pa.Field(ge=0)
    had_claim_60d: Series[int] = pa.Field(isin=[0, 1])
    renewal_in_30_days: Series[int] = pa.Field(isin=[0, 1])
    lost_quotation_count: Series[int] = pa.Field(ge=0)
    owns_A: Series[int] = pa.Field(isin=[0, 1])
    owns_B: Series[int] = pa.Field(isin=[0, 1])
    owns_C: Series[int] = pa.Field(isin=[0, 1])
    age: Series[int] = pa.Field(ge=18, le=75)
    income: Series[float] = pa.Field(ge=0)
    target: Series[int] = pa.Field(isin=[0, 1])

    class Config:
        coerce = True

def validate_features(df):
    try:
        NetflixFeatureSchema.validate(df, lazy=True)
        return True, "Validation passed"
    except pa.errors.SchemaErrors as err:
        return False, str(err)
