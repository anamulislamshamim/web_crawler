from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime, timezone


class Price(BaseModel):
    amount: Optional[float]
    currency: Optional[str]


# Define a function to generate the default timestamp
def get_current_time_utc():
    return datetime.now(timezone.utc)


class Book(BaseModel):
    name: str 
    description: Optional[str]
    category: Optional[str]
    price_including_tax: Optional[Price]
    price_excluding_tax: Optional[Price]
    availability: Optional[str]
    number_of_reviews: Optional[int]
    image_url: Optional[HttpUrl]
    rating: Optional[str]
    source_url: HttpUrl
    raw_html: str
    crawl_timestamp: datetime = Field(default_factory=get_current_time_utc)
    status: str = Field(default="new") # new, fetched, failed
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "A Light in the Attic",
                "description": "It's a delightful...",
                "category": "Poetry",
                "price_including_tax": {"amount": 51.77, "currency": "GBP"},
                "price_excluding_tax": {"amount": 45.17, "currency": "GBP"},
                "availability": "In stock (22 available)",
                "number_of_reviews": 0,
                "image_url": "http://books.toscrape.com/media/cache/...jpg",
                "rating": "Three",
                "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        }
    }
    