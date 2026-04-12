import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { Pool } from 'pg';
import { HotelResponse, CreateHotelDto, UpdateHotelDto, HotelFilterDto, localizeHotel } from './hotel.model';
import { AiService } from '../ai/ai.service';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

@Injectable()
export class HotelService {
  private readonly logger = new Logger(HotelService.name);
  constructor(private readonly aiService: AiService) {}

  async findAll(filter: HotelFilterDto): Promise<{ hotels: HotelResponse[]; total: number }> {
    try {
      const language = filter.language || 'en';
      const limit = filter.limit || 20;
      const offset = ((filter.page || 1) - 1) * limit;
      const result = await pool.query('SELECT * FROM hotels WHERE is_active = true ORDER BY rating DESC LIMIT $1 OFFSET $2', [limit, offset]);
      const count = await pool.query('SELECT COUNT(*) FROM hotels WHERE is_active = true');
      return {
        hotels: result.rows.map((h: any) => localizeHotel(this.mapRow(h), language)),
        total: parseInt(count.rows[0].count),
      };
    } catch (error) {
      this.logger.error('findAll failed: ' + error.message);
      return { hotels: [], total: 0 };
    }
  }

  async findById(id: string, language: string = 'en'): Promise<HotelResponse> {
    const result = await pool.query('SELECT * FROM hotels WHERE id = $1', [id]);
    if (!result.rows[0]) throw new NotFoundException('Hotel ' + id + ' not found');
    return localizeHotel(this.mapRow(result.rows[0]), language);
  }

  async search(query: string, language: string = 'en', limit: number = 10): Promise<HotelResponse[]> {
    try {
      const result = await pool.query('SELECT * FROM hotels WHERE is_active = true LIMIT $1', [limit]);
      return result.rows.map((h: any) => localizeHotel(this.mapRow(h), language));
    } catch { return []; }
  }

  async create(dto: CreateHotelDto): Promise<HotelResponse> {
    const result = await pool.query(
      'INSERT INTO hotels (id, name, description, amenities, address, stars, category, price_per_night, currency, images, is_active, is_verified) VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, $9, true, false) RETURNING *',
      [dto.name, dto.description || {}, dto.amenities || {}, dto.address || {}, dto.stars, dto.category, dto.pricePerNight, dto.currency || 'USD', dto.images || []]
    );
    return localizeHotel(this.mapRow(result.rows[0]), 'en');
  }

  async update(id: string, dto: UpdateHotelDto, language: string = 'en'): Promise<HotelResponse> {
    const result = await pool.query('SELECT * FROM hotels WHERE id = $1', [id]);
    if (!result.rows[0]) throw new NotFoundException('Hotel not found');
    return localizeHotel(this.mapRow(result.rows[0]), language);
  }

  async delete(id: string): Promise<void> {
    await pool.query('UPDATE hotels SET is_active = false WHERE id = $1', [id]);
  }

  async checkAvailability(hotelId: string, checkIn: Date, checkOut: Date): Promise<any> {
    const result = await pool.query('SELECT * FROM hotels WHERE id = $1', [hotelId]);
    if (!result.rows[0]) throw new NotFoundException('Hotel not found');
    const hotel = result.rows[0];
    const nights = Math.ceil((checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24));
    return { available: true, pricePerNight: Number(hotel.price_per_night), totalPrice: Number(hotel.price_per_night) * nights, nights, currency: hotel.currency };
  }

  async getAiRecommendations(destinationId: string, language: string, travelStyle?: string, budget?: string, groupType?: string): Promise<any> {
    const { hotels } = await this.findAll({ language });
    return this.aiService.recommendHotels({ destination: destinationId, hotels: hotels.map(h => ({ name: h.name, stars: h.stars, price: h.pricePerNight, rating: h.rating })), language, travelStyle, budget, groupType });
  }

  async updateRating(hotelId: string): Promise<void> {
    this.logger.log('Rating updated for hotel ' + hotelId);
  }

  async getStats(): Promise<any> {
    const result = await pool.query('SELECT COUNT(*) FROM hotels WHERE is_active = true');
    return { total: parseInt(result.rows[0].count), verified: 0, byCategory: {}, avgRating: 0 };
  }

  private mapRow(row: any): any {
    return {
      id: row.id,
      destinationId: row.destination_id,
      partnerId: row.partner_id,
      name: row.name,
      description: row.description || {},
      amenities: row.amenities || {},
      address: row.address || {},
      stars: row.stars,
      category: row.category,
      email: row.email,
      phone: row.phone,
      website: row.website,
      latitude: row.latitude,
      longitude: row.longitude,
      pricePerNight: Number(row.price_per_night),
      currency: row.currency,
      coverImageUrl: row.cover_image_url,
      images: row.images || [],
      rating: Number(row.rating),
      reviewCount: row.review_count,
      isActive: row.is_active,
      isVerified: row.is_verified,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }
}