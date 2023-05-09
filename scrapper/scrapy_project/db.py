from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///articles.sqlite')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Article(Base):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer,nullable=True)
    source = Column(String)
    url = Column(String, unique=True)
    title = Column(String)
    text = Column(String)
    timestamp = Column(DateTime)

if __name__ == '__main__':
    Article.metadata.create_all(engine)