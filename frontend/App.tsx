import { useState, useMemo, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Progress } from '@/components/ui/progress'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Dialog, DialogContent, DialogTrigger, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Search, TrendingDown, Bell, BarChart3, ShieldCheck, Globe, ChevronRight, ExternalLink, ArrowDown, ArrowUp, Minus, Star, Clock, Wind, Sun, Snowflake, Leaf, CloudRain, Heart, Menu, X, Filter } from 'lucide-react'

// ============================================================================
// TYPES
// ============================================================================

interface RetailerPrice {
  retailer: string
  retailerDisplay: string
  priceLocal: number
  currency: string
  priceGbp: number
  shippingGbp: number
  vatGbp: number
  totalLandedGbp: number
  inStock: boolean
  route: 'direct' | 'indirect'
  country: string
  url: string
  lastUpdated: string
}

interface PriceHistory {
  date: string
  price: number
}

interface FragranceProfile {
  accords: { name: string; strength: number }[]
  longevity: number
  sillage: number
  ratings: { overall: number; count: number }
  seasons: { spring: number; summer: number; fall: number; winter: number }
}

interface Product {
  id: string
  brand: string
  name: string
  sizeMl: number
  concentration: string
  typicalRetailGbp: number
  imageUrl: string
  gender: string
  notes: { top: string[]; heart: string[]; base: string[] }
  profile: FragranceProfile
  prices: RetailerPrice[]
  priceHistory: PriceHistory[]
  bestPrice: number
  savings: number
  savingsPct: number
}

// ============================================================================
// MOCK DATA (represents what API would return)
// ============================================================================

const MOCK_PRODUCTS: Product[] = [
  {
    id: 'pdm-layton-125-edp', brand: 'Parfums de Marly', name: 'Layton', sizeMl: 125, concentration: 'EDP',
    typicalRetailGbp: 195, imageUrl: '', gender: 'unisex',
    notes: { top: ['Apple', 'Bergamot', 'Mandarin'], heart: ['Jasmine', 'Violet', 'Geranium'], base: ['Vanilla', 'Sandalwood', 'Pepper'] },
    profile: { accords: [{ name: 'Warm Spicy', strength: 85 }, { name: 'Sweet', strength: 78 }, { name: 'Vanilla', strength: 72 }, { name: 'Woody', strength: 65 }, { name: 'Fresh Spicy', strength: 58 }], longevity: 82, sillage: 75, ratings: { overall: 4.6, count: 12400 }, seasons: { spring: 72, summer: 45, fall: 90, winter: 88 } },
    prices: [
      { retailer: 'nichegallerie', retailerDisplay: 'NicheGallerie', priceLocal: 189, currency: 'GBP', priceGbp: 189, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 189, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'fragrancebuy', retailerDisplay: 'FragranceBuy CA', priceLocal: 295, currency: 'CAD', priceGbp: 171.1, shippingGbp: 15, vatGbp: 37.2, totalLandedGbp: 223.3, inStock: true, route: 'indirect', country: 'CA', url: '#', lastUpdated: '2h ago' },
      { retailer: 'notino', retailerDisplay: 'Notino UK', priceLocal: 207, currency: 'GBP', priceGbp: 207, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 207, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'seescents', retailerDisplay: 'SeeScents', priceLocal: 195, currency: 'GBP', priceGbp: 195, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 195, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
    ],
    priceHistory: Array.from({ length: 30 }, (_, i) => ({ date: `2026-02-${String(i + 1).padStart(2, '0')}`, price: 189 + Math.random() * 20 - 10 })),
    bestPrice: 189, savings: 6, savingsPct: 3,
  },
  {
    id: 'creed-aventus-100-edp', brand: 'Creed', name: 'Aventus', sizeMl: 100, concentration: 'EDP',
    typicalRetailGbp: 310, imageUrl: '', gender: 'male',
    notes: { top: ['Pineapple', 'Bergamot', 'Blackcurrant'], heart: ['Birch', 'Jasmine', 'Patchouli'], base: ['Oak Moss', 'Musk', 'Ambergris'] },
    profile: { accords: [{ name: 'Fruity', strength: 88 }, { name: 'Woody', strength: 75 }, { name: 'Smoky', strength: 65 }, { name: 'Fresh', strength: 60 }, { name: 'Mossy', strength: 52 }], longevity: 78, sillage: 80, ratings: { overall: 4.5, count: 28500 }, seasons: { spring: 85, summer: 75, fall: 80, winter: 65 } },
    prices: [
      { retailer: 'seescents', retailerDisplay: 'SeeScents', priceLocal: 220, currency: 'GBP', priceGbp: 220, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 220, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'nichegallerie', retailerDisplay: 'NicheGallerie', priceLocal: 277, currency: 'GBP', priceGbp: 277, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 277, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'fragrancebuy', retailerDisplay: 'FragranceBuy CA', priceLocal: 415, currency: 'CAD', priceGbp: 240.7, shippingGbp: 15, vatGbp: 51.1, totalLandedGbp: 306.8, inStock: true, route: 'indirect', country: 'CA', url: '#', lastUpdated: '2h ago' },
      { retailer: 'notino', retailerDisplay: 'Notino UK', priceLocal: 297, currency: 'GBP', priceGbp: 297, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 297, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
    ],
    priceHistory: Array.from({ length: 30 }, (_, i) => ({ date: `2026-02-${String(i + 1).padStart(2, '0')}`, price: 220 + Math.random() * 30 - 15 })),
    bestPrice: 220, savings: 90, savingsPct: 29,
  },
  {
    id: 'mfk-br540-70-edp', brand: 'Maison Francis Kurkdjian', name: 'Baccarat Rouge 540', sizeMl: 70, concentration: 'EDP',
    typicalRetailGbp: 255, imageUrl: '', gender: 'unisex',
    notes: { top: ['Saffron', 'Jasmine'], heart: ['Amberwood', 'Ambergris'], base: ['Fir Resin', 'Cedar'] },
    profile: { accords: [{ name: 'Amber', strength: 90 }, { name: 'Sweet', strength: 82 }, { name: 'Woody', strength: 68 }, { name: 'Warm', strength: 65 }, { name: 'Floral', strength: 48 }], longevity: 88, sillage: 85, ratings: { overall: 4.4, count: 18200 }, seasons: { spring: 70, summer: 50, fall: 88, winter: 92 } },
    prices: [
      { retailer: 'nichegallerie', retailerDisplay: 'NicheGallerie', priceLocal: 189, currency: 'GBP', priceGbp: 189, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 189, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'notino', retailerDisplay: 'Notino UK', priceLocal: 218, currency: 'GBP', priceGbp: 218, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 218, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'fragrancebuy', retailerDisplay: 'FragranceBuy CA', priceLocal: 358, currency: 'CAD', priceGbp: 207.6, shippingGbp: 15, vatGbp: 44.5, totalLandedGbp: 267.1, inStock: true, route: 'indirect', country: 'CA', url: '#', lastUpdated: '2h ago' },
    ],
    priceHistory: Array.from({ length: 30 }, (_, i) => ({ date: `2026-02-${String(i + 1).padStart(2, '0')}`, price: 189 + Math.random() * 25 - 12 })),
    bestPrice: 189, savings: 66, savingsPct: 26,
  },
  {
    id: 'tf-tobacco-vanille-100-edp', brand: 'Tom Ford', name: 'Tobacco Vanille', sizeMl: 100, concentration: 'EDP',
    typicalRetailGbp: 270, imageUrl: '', gender: 'unisex',
    notes: { top: ['Tobacco Leaf', 'Spices'], heart: ['Vanilla', 'Tonka Bean', 'Cocoa'], base: ['Dried Fruits', 'Wood Sap'] },
    profile: { accords: [{ name: 'Sweet', strength: 92 }, { name: 'Tobacco', strength: 85 }, { name: 'Vanilla', strength: 80 }, { name: 'Warm Spicy', strength: 70 }, { name: 'Balsamic', strength: 55 }], longevity: 90, sillage: 82, ratings: { overall: 4.5, count: 15800 }, seasons: { spring: 45, summer: 20, fall: 92, winter: 95 } },
    prices: [
      { retailer: 'nichegallerie', retailerDisplay: 'NicheGallerie', priceLocal: 199, currency: 'GBP', priceGbp: 199, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 199, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'fragrancebuy', retailerDisplay: 'FragranceBuy CA', priceLocal: 369, currency: 'CAD', priceGbp: 214, shippingGbp: 15, vatGbp: 45.8, totalLandedGbp: 274.8, inStock: true, route: 'indirect', country: 'CA', url: '#', lastUpdated: '2h ago' },
      { retailer: 'notino', retailerDisplay: 'Notino UK', priceLocal: 235, currency: 'GBP', priceGbp: 235, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 235, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
    ],
    priceHistory: Array.from({ length: 30 }, (_, i) => ({ date: `2026-02-${String(i + 1).padStart(2, '0')}`, price: 199 + Math.random() * 18 - 9 })),
    bestPrice: 199, savings: 71, savingsPct: 26,
  },
  {
    id: 'initio-ofg-90-edp', brand: 'Initio', name: 'Oud for Greatness', sizeMl: 90, concentration: 'EDP',
    typicalRetailGbp: 285, imageUrl: '', gender: 'unisex',
    notes: { top: ['Agarwood', 'Saffron'], heart: ['Nutmeg', 'Lavender'], base: ['Musk', 'Patchouli'] },
    profile: { accords: [{ name: 'Oud', strength: 90 }, { name: 'Woody', strength: 82 }, { name: 'Warm Spicy', strength: 70 }, { name: 'Smoky', strength: 62 }, { name: 'Musky', strength: 55 }], longevity: 85, sillage: 78, ratings: { overall: 4.3, count: 6200 }, seasons: { spring: 55, summer: 30, fall: 85, winter: 90 } },
    prices: [
      { retailer: 'nichegallerie', retailerDisplay: 'NicheGallerie', priceLocal: 202, currency: 'GBP', priceGbp: 202, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 202, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'fragrancebuy', retailerDisplay: 'FragranceBuy CA', priceLocal: 385, currency: 'CAD', priceGbp: 223.3, shippingGbp: 15, vatGbp: 47.7, totalLandedGbp: 286, inStock: true, route: 'indirect', country: 'CA', url: '#', lastUpdated: '2h ago' },
      { retailer: 'notino', retailerDisplay: 'Notino UK', priceLocal: 267, currency: 'GBP', priceGbp: 267, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 267, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
    ],
    priceHistory: Array.from({ length: 30 }, (_, i) => ({ date: `2026-02-${String(i + 1).padStart(2, '0')}`, price: 202 + Math.random() * 22 - 11 })),
    bestPrice: 202, savings: 83, savingsPct: 29,
  },
  {
    id: 'xerjoff-naxos-100-edp', brand: 'Xerjoff', name: 'Naxos', sizeMl: 100, concentration: 'EDP',
    typicalRetailGbp: 195, imageUrl: '', gender: 'unisex',
    notes: { top: ['Lavender', 'Bergamot', 'Lemon'], heart: ['Cinnamon', 'Cashmeran', 'Honey'], base: ['Tobacco', 'Vanilla', 'Tonka Bean'] },
    profile: { accords: [{ name: 'Tobacco', strength: 85 }, { name: 'Sweet', strength: 80 }, { name: 'Lavender', strength: 75 }, { name: 'Honey', strength: 68 }, { name: 'Vanilla', strength: 62 }], longevity: 86, sillage: 76, ratings: { overall: 4.5, count: 5100 }, seasons: { spring: 60, summer: 35, fall: 88, winter: 90 } },
    prices: [
      { retailer: 'nichegallerie', retailerDisplay: 'NicheGallerie', priceLocal: 149, currency: 'GBP', priceGbp: 149, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 149, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'notino', retailerDisplay: 'Notino UK', priceLocal: 172, currency: 'GBP', priceGbp: 172, shippingGbp: 0, vatGbp: 0, totalLandedGbp: 172, inStock: true, route: 'direct', country: 'UK', url: '#', lastUpdated: '2h ago' },
      { retailer: 'fragrancebuy', retailerDisplay: 'FragranceBuy CA', priceLocal: 275, currency: 'CAD', priceGbp: 159.5, shippingGbp: 15, vatGbp: 34.9, totalLandedGbp: 209.4, inStock: true, route: 'indirect', country: 'CA', url: '#', lastUpdated: '2h ago' },
    ],
    priceHistory: Array.from({ length: 30 }, (_, i) => ({ date: `2026-02-${String(i + 1).padStart(2, '0')}`, price: 149 + Math.random() * 15 - 7 })),
    bestPrice: 149, savings: 46, savingsPct: 24,
  },
]

// ============================================================================
// UTILITY COMPONENTS
// ============================================================================

function PriceChange({ current, previous }: { current: number; previous: number }) {
  const diff = current - previous
  const pct = ((diff / previous) * 100).toFixed(1)
  if (Math.abs(diff) < 1) return <span className="text-zinc-500 text-xs flex items-center gap-0.5"><Minus className="w-3 h-3" /> Stable</span>
  if (diff < 0) return <span className="text-emerald-500 text-xs flex items-center gap-0.5"><ArrowDown className="w-3 h-3" /> {pct}%</span>
  return <span className="text-red-400 text-xs flex items-center gap-0.5"><ArrowUp className="w-3 h-3" /> +{pct}%</span>
}

function AccordBar({ name, strength }: { name: string; strength: number }) {
  const colors: Record<string, string> = {
    'Warm Spicy': 'bg-orange-500', 'Sweet': 'bg-pink-400', 'Vanilla': 'bg-amber-300',
    'Woody': 'bg-amber-700', 'Fresh Spicy': 'bg-teal-500', 'Fruity': 'bg-rose-400',
    'Smoky': 'bg-zinc-500', 'Fresh': 'bg-cyan-400', 'Mossy': 'bg-green-600',
    'Amber': 'bg-amber-500', 'Floral': 'bg-purple-400', 'Tobacco': 'bg-amber-800',
    'Oud': 'bg-stone-700', 'Musky': 'bg-zinc-400', 'Balsamic': 'bg-red-800',
    'Honey': 'bg-yellow-500', 'Lavender': 'bg-violet-400',
  }
  const color = colors[name] || 'bg-zinc-500'
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-zinc-400 truncate">{name}</span>
      <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${strength}%` }} />
      </div>
      <span className="text-zinc-500 w-7 text-right">{strength}%</span>
    </div>
  )
}

function SeasonIcon({ season, value }: { season: string; value: number }) {
  const icons: Record<string, typeof Sun> = { spring: Leaf, summer: Sun, fall: CloudRain, winter: Snowflake }
  const Icon = icons[season] || Sun
  const opacity = value > 70 ? 'text-zinc-100' : value > 40 ? 'text-zinc-400' : 'text-zinc-600'
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <div className="flex flex-col items-center gap-0.5">
            <Icon className={`w-3.5 h-3.5 ${opacity}`} />
            <span className="text-[10px] text-zinc-500">{value}%</span>
          </div>
        </TooltipTrigger>
        <TooltipContent><p className="capitalize">{season}: {value}% recommended</p></TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

function MiniSparkline({ data, width = 120, height = 32 }: { data: PriceHistory[]; width?: number; height?: number }) {
  if (!data.length) return null
  const prices = data.map(d => d.price)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const points = prices.map((p, i) => `${(i / (prices.length - 1)) * width},${height - ((p - min) / range) * (height - 4) - 2}`).join(' ')
  return (
    <svg width={width} height={height} className="opacity-60">
      <polyline fill="none" stroke="rgb(34 197 94)" strokeWidth="1.5" points={points} />
    </svg>
  )
}

// ============================================================================
// PRODUCT CARD
// ============================================================================

function ProductCard({ product, onSelect }: { product: Product; onSelect: (p: Product) => void }) {
  const bestRetailer = product.prices[0]
  const prevPrice = product.priceHistory.length > 7 ? product.priceHistory[product.priceHistory.length - 8].price : product.bestPrice

  return (
    <Card className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-all cursor-pointer group" onClick={() => onSelect(product)}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <p className="text-[11px] text-zinc-500 uppercase tracking-wider font-medium">{product.brand}</p>
            <h3 className="text-base font-semibold text-zinc-100 truncate">{product.name}</h3>
            <p className="text-xs text-zinc-500">{product.sizeMl}ml · {product.concentration}</p>
          </div>
          <div className="text-right ml-3 shrink-0">
            <p className="text-xl font-bold text-zinc-100">£{product.bestPrice}</p>
            <p className="text-xs text-zinc-500 line-through">RRP £{product.typicalRetailGbp}</p>
          </div>
        </div>

        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border-0 ${product.savingsPct >= 25 ? 'bg-emerald-500/15 text-emerald-400' : product.savingsPct >= 15 ? 'bg-amber-500/15 text-amber-400' : 'bg-zinc-500/15 text-zinc-400'}`}>
              {product.savingsPct >= 25 ? 'HOT DEAL' : product.savingsPct >= 15 ? 'GOOD DEAL' : 'SAVE'} {product.savingsPct}%
            </Badge>
            <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-0 bg-zinc-800 text-zinc-400">
              {bestRetailer?.route === 'direct' ? '🇬🇧 Direct' : '🌍 Import'}
            </Badge>
          </div>
          <PriceChange current={product.bestPrice} previous={prevPrice} />
        </div>

        <Separator className="bg-zinc-800 mb-3" />

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] text-zinc-500">Best at</span>
            <span className="text-[11px] text-zinc-300 font-medium">{bestRetailer?.retailerDisplay}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[11px] text-zinc-500">{product.prices.length} retailers</span>
            <ChevronRight className="w-3 h-3 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
          </div>
        </div>

        <div className="mt-2">
          <MiniSparkline data={product.priceHistory} />
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// PRODUCT DETAIL
// ============================================================================

function ProductDetail({ product, onClose }: { product: Product; onClose: () => void }) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-zinc-500 uppercase tracking-wider font-medium">{product.brand}</p>
            <h2 className="text-2xl font-bold text-zinc-100">{product.name}</h2>
            <p className="text-sm text-zinc-400">{product.sizeMl}ml · {product.concentration} · {product.gender}</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-zinc-100">£{product.bestPrice}</p>
            <p className="text-sm text-zinc-500">RRP <span className="line-through">£{product.typicalRetailGbp}</span></p>
            <Badge className="mt-1 bg-emerald-500/15 text-emerald-400 border-0">Save £{product.savings} ({product.savingsPct}%)</Badge>
          </div>
        </div>
      </div>

      {/* Price Comparison Table */}
      <div>
        <h3 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4" /> Price Comparison
        </h3>
        <div className="space-y-2">
          {product.prices.map((price, i) => (
            <div key={price.retailer} className={`flex items-center justify-between p-3 rounded-lg ${i === 0 ? 'bg-emerald-500/5 border border-emerald-500/20' : 'bg-zinc-800/50'}`}>
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-xs font-mono text-zinc-500 w-4">{i + 1}</span>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-zinc-200">{price.retailerDisplay}</span>
                    <Badge variant="outline" className="text-[9px] px-1 py-0 border-zinc-700 text-zinc-500">
                      {price.route === 'direct' ? 'Direct' : 'Import'}
                    </Badge>
                  </div>
                  {price.route === 'indirect' && (
                    <p className="text-[10px] text-zinc-500 mt-0.5">
                      {price.currency} {price.priceLocal.toFixed(0)} + £{price.shippingGbp} shipping + £{price.vatGbp.toFixed(0)} VAT
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <div className="text-right">
                  <p className={`text-sm font-bold ${i === 0 ? 'text-emerald-400' : 'text-zinc-300'}`}>£{price.totalLandedGbp.toFixed(0)}</p>
                  <p className="text-[10px] text-zinc-500">{price.lastUpdated}</p>
                </div>
                <a href={price.url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}>
                  <ExternalLink className="w-3.5 h-3.5 text-zinc-500 hover:text-zinc-300" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Fragrance Profile */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2">
            <Wind className="w-4 h-4" /> Scent Profile
          </h3>
          <div className="space-y-1.5">
            {product.profile.accords.map(accord => (
              <AccordBar key={accord.name} name={accord.name} strength={accord.strength} />
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-zinc-300 mb-3">Performance</h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-zinc-400">Longevity</span>
                <span className="text-zinc-300">{product.profile.longevity}%</span>
              </div>
              <Progress value={product.profile.longevity} className="h-1.5" />
            </div>
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-zinc-400">Sillage</span>
                <span className="text-zinc-300">{product.profile.sillage}%</span>
              </div>
              <Progress value={product.profile.sillage} className="h-1.5" />
            </div>
            <div className="flex items-center gap-1 mt-1">
              <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
              <span className="text-sm font-medium text-zinc-200">{product.profile.ratings.overall}</span>
              <span className="text-xs text-zinc-500">({(product.profile.ratings.count / 1000).toFixed(1)}k reviews)</span>
            </div>
            <div className="flex items-center gap-3 mt-2">
              {Object.entries(product.profile.seasons).map(([season, value]) => (
                <SeasonIcon key={season} season={season} value={value} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Notes Pyramid */}
      <div>
        <h3 className="text-sm font-semibold text-zinc-300 mb-3">Notes</h3>
        <div className="space-y-2">
          {(['top', 'heart', 'base'] as const).map(layer => (
            <div key={layer} className="flex items-start gap-2">
              <span className="text-[10px] uppercase text-zinc-500 w-10 pt-0.5 shrink-0">{layer}</span>
              <div className="flex flex-wrap gap-1">
                {product.notes[layer].map(note => (
                  <Badge key={note} variant="outline" className="text-[10px] px-1.5 py-0 border-zinc-700 text-zinc-400 bg-zinc-800/50">
                    {note}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Price History Chart */}
      <div>
        <h3 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2">
          <TrendingDown className="w-4 h-4" /> 30-Day Price Trend
        </h3>
        <div className="bg-zinc-800/30 rounded-lg p-3">
          <MiniSparkline data={product.priceHistory} width={400} height={60} />
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white">
          <Bell className="w-4 h-4 mr-2" /> Set Price Alert
        </Button>
        <Button variant="outline" className="flex-1 border-zinc-700 text-zinc-300 hover:bg-zinc-800">
          <Heart className="w-4 h-4 mr-2" /> Add to Watchlist
        </Button>
      </div>
    </div>
  )
}

// ============================================================================
// STATS BAR
// ============================================================================

function StatsBar() {
  return (
    <div className="grid grid-cols-4 gap-3">
      {[
        { label: 'Products tracked', value: '114', icon: Search },
        { label: 'Retailers monitored', value: '25', icon: Globe },
        { label: 'Avg. savings', value: '22%', icon: TrendingDown },
        { label: 'Last scan', value: '2h ago', icon: Clock },
      ].map(stat => (
        <div key={stat.label} className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 flex items-center gap-3">
          <stat.icon className="w-4 h-4 text-zinc-500 shrink-0" />
          <div>
            <p className="text-lg font-bold text-zinc-100">{stat.value}</p>
            <p className="text-[10px] text-zinc-500">{stat.label}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// MAIN APP
// ============================================================================

export default function App() {
  const [searchQuery, setSearchQuery] = useState('')
  const [brandFilter, setBrandFilter] = useState('all')
  const [sortBy, setSortBy] = useState('savings')
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const brands = useMemo(() => {
    const b = [...new Set(MOCK_PRODUCTS.map(p => p.brand))].sort()
    return b
  }, [])

  const filteredProducts = useMemo(() => {
    let filtered = MOCK_PRODUCTS
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(q) ||
        p.brand.toLowerCase().includes(q) ||
        p.notes.top.some(n => n.toLowerCase().includes(q)) ||
        p.notes.heart.some(n => n.toLowerCase().includes(q)) ||
        p.notes.base.some(n => n.toLowerCase().includes(q))
      )
    }
    if (brandFilter !== 'all') {
      filtered = filtered.filter(p => p.brand === brandFilter)
    }
    const sorted = [...filtered]
    switch (sortBy) {
      case 'savings': sorted.sort((a, b) => b.savingsPct - a.savingsPct); break
      case 'price_low': sorted.sort((a, b) => a.bestPrice - b.bestPrice); break
      case 'price_high': sorted.sort((a, b) => b.bestPrice - a.bestPrice); break
      case 'name': sorted.sort((a, b) => a.name.localeCompare(b.name)); break
      case 'brand': sorted.sort((a, b) => a.brand.localeCompare(b.brand) || a.name.localeCompare(b.name)); break
    }
    return sorted
  }, [searchQuery, brandFilter, sortBy])

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-zinc-950/95 backdrop-blur-sm border-b border-zinc-800/50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight">
              <span className="text-emerald-400">OL</span><span className="text-zinc-100">FEX</span>
            </h1>
            <span className="text-[10px] text-zinc-600 hidden sm:inline">Olfactory Exchange</span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm">
            <a href="#" className="text-zinc-300 hover:text-zinc-100 transition-colors font-medium">Deals</a>
            <a href="#" className="text-zinc-500 hover:text-zinc-300 transition-colors">Brands</a>
            <a href="#" className="text-zinc-500 hover:text-zinc-300 transition-colors">Alerts</a>
            <a href="#" className="text-zinc-500 hover:text-zinc-300 transition-colors">Watchlist</a>
          </nav>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 hidden sm:flex">
              <Bell className="w-4 h-4" />
            </Button>
            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs h-8">
              Sign Up Free
            </Button>
            <Button variant="ghost" size="sm" className="md:hidden text-zinc-400" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              <Menu className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* Hero */}
        <div className="text-center py-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-zinc-100 mb-2">
            Find the best niche fragrance prices
          </h2>
          <p className="text-zinc-400 text-sm max-w-lg mx-auto">
            Real-time price comparison across 25 retailers. Landed costs calculated for UK buyers —
            including shipping, import VAT, and currency conversion.
          </p>
        </div>

        {/* Stats */}
        <StatsBar />

        {/* Search + Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <Input
              placeholder="Search fragrances, brands, or notes..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-10 bg-zinc-900 border-zinc-800 text-zinc-200 placeholder:text-zinc-600 h-10"
            />
          </div>
          <Select value={brandFilter} onValueChange={setBrandFilter}>
            <SelectTrigger className="w-full sm:w-48 bg-zinc-900 border-zinc-800 text-zinc-300 h-10">
              <SelectValue placeholder="All Brands" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              <SelectItem value="all" className="text-zinc-300">All Brands</SelectItem>
              {brands.map(b => (
                <SelectItem key={b} value={b} className="text-zinc-300">{b}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-full sm:w-44 bg-zinc-900 border-zinc-800 text-zinc-300 h-10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              <SelectItem value="savings" className="text-zinc-300">Best Savings</SelectItem>
              <SelectItem value="price_low" className="text-zinc-300">Price: Low → High</SelectItem>
              <SelectItem value="price_high" className="text-zinc-300">Price: High → Low</SelectItem>
              <SelectItem value="name" className="text-zinc-300">Name A → Z</SelectItem>
              <SelectItem value="brand" className="text-zinc-300">Brand</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Results count */}
        <div className="flex items-center justify-between">
          <p className="text-xs text-zinc-500">{filteredProducts.length} fragrances</p>
          <div className="flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-500" />
            <span className="text-[10px] text-zinc-500">Prices verified {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</span>
          </div>
        </div>

        {/* Product Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProducts.map(product => (
            <ProductCard key={product.id} product={product} onSelect={setSelectedProduct} />
          ))}
        </div>

        {filteredProducts.length === 0 && (
          <div className="text-center py-16">
            <p className="text-zinc-500">No fragrances found matching your search.</p>
          </div>
        )}
      </main>

      {/* Product Detail Sheet */}
      <Sheet open={!!selectedProduct} onOpenChange={() => setSelectedProduct(null)}>
        <SheetContent side="right" className="w-full sm:max-w-lg bg-zinc-950 border-zinc-800 overflow-y-auto">
          {selectedProduct && <ProductDetail product={selectedProduct} onClose={() => setSelectedProduct(null)} />}
        </SheetContent>
      </Sheet>

      {/* Footer */}
      <footer className="border-t border-zinc-800/50 mt-16">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold"><span className="text-emerald-400">OL</span>FEX</h3>
              <p className="text-xs text-zinc-600 mt-1">Olfactory Exchange — Real prices, real savings.</p>
            </div>
            <div className="flex items-center gap-4 text-xs text-zinc-600">
              <span>olfex.app</span>
              <span>·</span>
              <span>olfex.co.uk</span>
              <span>·</span>
              <span>© 2026 Peptyl Ltd</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
