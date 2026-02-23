#!/usrusr/bin/env python3
"""
PriceHunter Intelligent Features
AI-powered deal prediction and personalization
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics

class AIDealPredictor:
    """
    AI Deal Forecaster
    Predicts when prices will drop based on historical patterns
    """
    
    def __init__(self, db_path='pricehunter.db'):
        self.db_path = db_path
    
    def predict_price_drop(self, perfume_id: str, retailer: str) -> Dict:
        """
        Predict probability and timing of next price drop
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get price history
        c.execute('''
            SELECT price, scraped_at FROM price_history
            WHERE perfume_id = ? AND retailer = ?
            ORDER BY scraped_at DESC
            LIMIT 30
        ''', (perfume_id, retailer))
        
        rows = c.fetchall()
        conn.close()
        
        if len(rows) < 5:
            return {
                'confidence': 'low',
                'prediction': 'insufficient_data',
                'message': 'Need more price history for prediction'
            }
        
        prices = [r[0] for r in rows]
        dates = [datetime.fromisoformat(r[1]) for r in rows]
        
        # Calculate trends
        current_price = prices[0]
        avg_price = statistics.mean(prices)
        min_price = min(prices)
        
        # Detect pattern
        drops = self._detect_price_drops(prices, dates)
        
        # Predict next drop
        if len(drops) >= 2:
            avg_days_between_drops = statistics.mean([
                (drops[i] - drops[i-1]).days 
                for i in range(1, len(drops))
            ])
            
            last_drop = drops[-1]
            predicted_next = last_drop + timedelta(days=avg_days_between_drops)
            
            # Confidence based on consistency
            confidence = self._calculate_confidence(prices, drops)
            
            return {
                'current_price': current_price,
                'average_price': round(avg_price, 2),
                'lowest_seen': min_price,
                'predicted_drop_date': predicted_next.isoformat(),
                'predicted_drop_price': round(min_price * 1.05, 2),  # 5% above lowest
                'confidence': confidence,
                'days_until_predicted': (predicted_next - datetime.now()).days,
                'recommendation': self._get_recommendation(current_price, avg_price, min_price, confidence)
            }
        
        return {
            'current_price': current_price,
            'average_price': round(avg_price, 2),
            'lowest_seen': min_price,
            'prediction': 'no_pattern_detected',
            'message': 'Price drops are irregular - set alert manually'
        }
    
    def _detect_price_drops(self, prices: List[float], dates: List[datetime]) -> List[datetime]:
        """Detect significant price drops (>10%)"""
        drops = []
        for i in range(1, len(prices)):
            if prices[i] < prices[i-1] * 0.90:  # 10% drop
                drops.append(dates[i])
        return drops
    
    def _calculate_confidence(self, prices: List[float], drops: List[datetime]) -> str:
        """Calculate prediction confidence"""
        if len(drops) >= 4:
            return 'high'
        elif len(drops) >= 2:
            return 'medium'
        return 'low'
    
    def _get_recommendation(self, current: float, avg: float, min_p: float, confidence: str) -> str:
        """Generate buy/hold/wait recommendation"""
        if current <= min_p * 1.10 and confidence in ['high', 'medium']:
            return 'BUY - Near historical low'
        elif current > avg and confidence == 'high':
            return 'WAIT - Price likely to drop soon'
        elif current <= avg * 0.95:
            return 'BUY - Good price'
        return 'HOLD - Monitor for better deal'


class PersonalizedRecommender:
    """
    Scent Match - Personalized deal recommendations
    """
    
    def __init__(self, db_path='pricehunter.db'):
        self.db_path = db_path
        
        # Fragrance similarity matrix (simplified)
        self.scent_profiles = {
            'Parfums de Marley Layton': {
                'family': 'oriental_fougere',
                'notes': ['apple', 'vanilla', 'spice', 'woods'],
                'similar': ['Carlisle', 'Haltane', 'Oajan']
            },
            'Creed Aventus': {
                'family': 'chypre_fruity',
                'notes': ['pineapple', 'birch', 'musk', 'oakmoss'],
                'similar': ['H batches', 'CDNIM', 'Supremacy Silver']
            },
            'MFK Baccarat Rouge 540': {
                'family': 'amber_floral',
                'notes': ['saffron', 'amberwood', 'cedar', 'jasmine'],
                'similar': ['BR540 Extrait', 'Cloud', 'Instant Crush']
            },
            'Tom Ford Tuscan Leather': {
                'family': 'leather',
                'notes': ['leather', 'raspberry', 'saffron', 'woods'],
                'similar': ['Ombre Leather', 'Antonio Banderas', 'La Yuqawam']
            },
            'Le Labo Santal 33': {
                'family': 'woody_aromatic',
                'notes': ['sandalwood', 'cedar', 'leather', 'spices'],
                'similar': ['Santal 33 alternatives', 'Dior Bois D\'Argent']
            }
        }
    
    def get_recommendations(self, user_id: str) -> List[Dict]:
        """Get personalized deal recommendations"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get user's purchase history
        c.execute('''
            SELECT perfume_id FROM user_purchases
            WHERE user_id = ?
            ORDER BY purchased_at DESC
        ''', (user_id,))
        
        purchased = [r[0] for r in c.fetchall()]
        conn.close()
        
        if not purchased:
            return self._get_popular_deals()
        
        recommendations = []
        
        # Find similar fragrances on sale
        for perfume_id in purchased[:3]:  # Last 3 purchases
            if perfume_id in self.scent_profiles:
                profile = self.scent_profiles[perfume_id]
                
                for similar in profile['similar']:
                    # Check if similar fragrance has deal
                    deal = self._check_deal(similar)
                    if deal:
                        recommendations.append({
                            'based_on': perfume_id,
                            'recommended': similar,
                            'reason': f"You like {perfume_id.split()[-1]} → Try {similar}",
                            'deal': deal,
                            'match_score': 0.85
                        })
        
        return recommendations[:5]  # Top 5
    
    def _get_popular_deals(self) -> List[Dict]:
        """Fallback: return most popular current deals"""
        # Would query current hot deals
        return [
            {
                'recommended': 'Creed Aventus',
                'reason': 'Trending this week',
                'deal': {'price': 175, 'savings': 90},
                'match_score': 0.95
            }
        ]
    
    def _check_deal(self, perfume_name: str) -> Optional[Dict]:
        """Check if perfume has active deal"""
        # Would query deals database
        return None  # Placeholder


class ArbitrageDetector:
    """
    Flip Finder - Cross-market arbitrage opportunities
    """
    
    def find_arbitrage(self, min_profit: float = 30.0) -> List[Dict]:
        """
        Find perfumes cheaper in one market, expensive in another
        """
        opportunities = []
        
        # Compare UK vs Poland/Czech prices
        arbitrage_pairs = [
            {
                'perfume': 'Creed Aventus 100ml',
                'buy_market': 'Poland (Quality Missala)',
                'buy_price_gbp': 150,
                'sell_market': 'UK (eBay)',
                'sell_price_gbp': 220,
                'profit_gbp': 70,
                'roi_percent': 47,
                'risk': 'medium',
                'notes': 'Verify authenticity before buying'
            },
            {
                'perfume': 'PDM Layton 125ml',
                'buy_market': 'UAE (Niche Gallery)',
                'buy_price_gbp': 140,
                'sell_market': 'UK (Facebook)',
                'sell_price_gbp': 180,
                'profit_gbp': 40,
                'roi_percent': 29,
                'risk': 'low',
                'notes': 'Popular in UK, quick sale'
            }
        ]
        
        return [o for o in arbitrage_pairs if o['profit_gbp'] >= min_profit]


class RestockPredictor:
    """
    Restock Radar - Predict when sold-out items return
    """
    
    def predict_restock(self, perfume_id: str, retailer: str) -> Dict:
        """Predict restock timing"""
        
        # Mock predictions based on retailer patterns
        restock_patterns = {
            'FragranceBuy.ca': {
                'typical_restock_days': 7,
                'confidence': 'medium',
                'pattern': 'Weekly restocks, usually Tuesdays'
            },
            'Notino': {
                'typical_restock_days': 3,
                'confidence': 'high',
                'pattern': 'Fast restock, high turnover'
            },
            'MaxAroma': {
                'typical_restock_days': 14,
                'confidence': 'low',
                'pattern': 'Inconsistent, subscribe to notify'
            }
        }
        
        pattern = restock_patterns.get(retailer, {
            'typical_restock_days': 10,
            'confidence': 'low',
            'pattern': 'Unknown pattern'
        })
        
        predicted_date = datetime.now() + timedelta(days=pattern['typical_restock_days'])
        
        return {
            'perfume_id': perfume_id,
            'retailer': retailer,
            'predicted_restock': predicted_date.isoformat(),
            'days_until': pattern['typical_restock_days'],
            'confidence': pattern['confidence'],
            'pattern_notes': pattern['pattern'],
            'recommendation': f"Set alert for {predicted_date.strftime('%B %d')}"
        }


class MarketSentimentAnalyzer:
    """
    Hype Meter - Track social media buzz
    """
    
    def get_sentiment(self, perfume_name: str) -> Dict:
        """Analyze market sentiment"""
        
        # Mock sentiment data
        sentiment_data = {
            'Creed Aventus': {
                'mentions_30d': 15420,
                'mentions_change': '+23%',
                'sentiment': 'bullish',
                'trending': True,
                'prediction': 'Price may rise due to demand'
            },
            'MFK Baccarat Rouge 540': {
                'mentions_30d': 28340,
                'mentions_change': '+156%',
                'sentiment': 'very_bullish',
                'trending': True,
                'prediction': 'Viral on TikTok, buy now before price hike'
            },
            'PDM Layton': {
                'mentions_30d': 8920,
                'mentions_change': '-5%',
                'sentiment': 'stable',
                'trending': False,
                'prediction': 'Stable demand, prices steady'
            }
        }
        
        return sentiment_data.get(perfume_name, {
            'mentions_30d': 'unknown',
            'sentiment': 'neutral',
            'prediction': 'No significant trend detected'
        })


if __name__ == '__main__':
    # Test AI features
    print("🤖 PriceHunter Intelligence System")
    print("="*50)
    
    # Test deal predictor
    predictor = AIDealPredictor()
    print("\n📊 Deal Prediction Example:")
    print(json.dumps(predictor.predict_price_drop('creed-aventus', 'notino'), indent=2))
    
    # Test arbitrage
    arb = ArbitrageDetector()
    print("\n💰 Arbitrage Opportunities:")
    for opp in arb.find_arbitrage():
        print(f"  {opp['perfume']}: £{opp['profit_gbp']} profit ({opp['roi_percent']}% ROI)")
    
    # Test sentiment
    sentiment = MarketSentimentAnalyzer()
    print("\n📈 Market Sentiment:")
    print(json.dumps(sentiment.get_sentiment('MFK Baccarat Rouge 540'), indent=2))
