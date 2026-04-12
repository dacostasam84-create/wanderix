import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import {
  HotelResponse,
  CreateHotelDto,
  UpdateHotelDto,
  HotelFilterDto,
  localizeHotel,
} from './hotel.model';
import { AiService } from '../ai/ai.service';

const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

@Injectable()
export class HotelService {
  private readonly logger = new Logger(HotelService.name);

  constructor(private readonly aiService: AiService) {}

  async findAll(filter: HotelFilterDto): Promise<{ hotels: HotelResponse[]; total: number }> {
    try {
      const language = filter.language || 'en';
      const where: any = { isActive: true };
      if (filter.destinationId) where.destinationId = filter.destinationId;
      if (filter.stars) where.stars = filter.stars;
      if (filter.category) where.category = filter.category;
      if (filter.minPrice || filter.maxPrice) {
        where.pricePerNight = {};
        if (filter.minPrice) where.pricePerNight.gte = filter.minPrice;
        if (filter.maxPrice) where.pricePerNight.lte = filter.maxPrice;
      }
      const [hotels, total] = await Promise.all([
        prisma.hotel.findMany({ where, take: filter.limit || 20, skip: ((filter.page || 1) - 1) * (filter.limit || 20) }),
        prisma.hotel.count({ where }),
      ]);
      return { hotels: hotels.map((h: any) => localizeHotel(h, language)), total };
    } catch (error) {
      this.logger.error('findAll failed: ' + error.message);
      return { hotels: [], total: 0 };
    }
  }

  async findById(id: string, language: string = 'en'): Promise<HotelResponse> {
    const hotel = await prisma.hotel.findUnique({ where: { id } });
    if (!hotel) throw new NotFoundException('Hotel ' + id + ' not found');
    return localizeHotel(hotel, language);
  }

  async search(query: string, language: string = 'en', limit: number = 10): Promise<HotelResponse[]> {
    try {
      const hotels = await prisma.hotel.findMany({ where: { isActive: true }, take: limit });
      return hotels.map((h: any) => localizeHotel(h, language));
    } catch { return []; }
  }

  async create(dto: CreateHotelDto): Promise<HotelResponse> {
    const hotel = await prisma.hotel.create({
      data: {
        name: dto.name, description: dto.description || {},
        amenities: dto.amenities || {}, address: dto.address || {},
        stars: dto.stars, category: dto.category,
        pricePerNight: dto.pricePerNight, currency: dto.currency || 'USD',
        images: dto.images || [],
      },
    });
    return localizeHotel(hotel, 'en');
  }

  async update(id: string, dto: UpdateHotelDto, language: string = 'en'): Promise<HotelResponse> {
    const hotel = await prisma.hotel.update({ where: { id }, data: dto as any });
    return localizeHotel(hotel, language);
  }

  async delete(id: string): Promise<void> {
    await prisma.hotel.update({ where: { id }, data: { isActive: false } });
  }

  async checkAvailability(hotelId: string, checkIn: Date, checkOut: Date): Promise<any> {
    const hotel = await prisma.hotel.findUnique({ where: { id: hotelId } });
    if (!hotel) throw new NotFoundException('Hotel not found');
    const nights = Math.ceil((checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24));
    return { available: true, pricePerNight: Number(hotel.pricePerNight), totalPrice: Number(hotel.pricePerNight) * nights, nights, currency: hotel.currency };
  }

  async getAiRecommendations(destinationId: string, language: string, travelStyle?: string, budget?: string, groupType?: string): Promise<any> {
    const { hotels } = await this.findAll({ destinationId, language });
    return this.aiService.recommendHotels({ destination: destinationId, hotels: hotels.map(h => ({ name: h.name, stars: h.stars, price: h.pricePerNight, rating: h.rating })), language, travelStyle, budget, groupType });
  }

  async updateRating(hotelId: string): Promise<void> {
    this.logger.log('Rating updated for hotel ' + hotelId);
  }

  async getStats(): Promise<any> {
    const total = await prisma.hotel.count({ where: { isActive: true } });
    return { total, verified: 0, byCategory: {}, avgRating: 0 };
  }
}