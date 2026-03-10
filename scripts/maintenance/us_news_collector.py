
import feedparser
from textblob import TextBlob
from datetime import datetime
import time
import re
import urllib.parse

class USNewsCollector:
    def __init__(self):
        self.base_url = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    def get_news(self, stock_code, company_name=None, limit=5):
        """
        특정 종목에 대한 최신 뉴스 수집 및 감성 분석
        """
        query_str = f"{stock_code} stock"
        if company_name:
            query_str += f" OR {company_name}"
            
        # URL Encoding
        encoded_query = urllib.parse.quote(query_str)
        url = self.base_url.format(query=encoded_query)
        
        try:
            feed = feedparser.parse(url)
            news_list = []
            
            for entry in feed.entries[:limit]:
                title = entry.title
                link = entry.link
                published = entry.published_parsed
                
                # 날짜 변환
                if published:
                    news_date = datetime(*published[:6])
                else:
                    news_date = datetime.now()

                # 감성 분석
                sentiment_score = self.analyze_sentiment(title)
                sentiment_label = self.get_sentiment_label(sentiment_score)
                
                news_list.append({
                    'stock_code': stock_code,
                    'news_date': news_date,
                    'title': title,
                    'link': link,
                    'source': 'Google News',
                    'sentiment_score': sentiment_score,
                    'sentiment_label': sentiment_label
                })
                
            return news_list
            
        except Exception as e:
            print(f"[ERROR] 뉴스 수집 실패 ({stock_code}): {e}")
            return []

    def analyze_sentiment(self, text):
        """
        텍스트 감성 분석 (-1.0 ~ 1.0)
        """
        if not text:
            return 0.0
        
        # 간단한 전처리
        clean_text = re.sub(r'<[^>]+>', '', text) # HTML 태그 제거
        blob = TextBlob(clean_text)
        return round(blob.sentiment.polarity, 2)

    def get_sentiment_label(self, score):
        if score >= 0.1:
            return 'Positive'
        elif score <= -0.1:
            return 'Negative'
        else:
            return 'Neutral'

if __name__ == "__main__":
    # 테스트
    collector = USNewsCollector()
    news = collector.get_news("AAPL", "Apple Inc", limit=3)
    for n in news:
        print(f"[{n['news_date']}] {n['title']} ({n['sentiment_label']}: {n['sentiment_score']})")
