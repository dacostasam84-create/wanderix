import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import {
  HotelModel,
  HotelResponse,
  CreateHotelDto,
  UpdateHotelDto,
  HotelFilterDto,
  localizeHotel,
} from './hotel.model';
import { AiService } from '../ai/ai.service';

@Injectable()
export class HotelService {
  private readonly logger = new Logger(HotelService.name);

  constructor(private readonly aiService: AiService) {}

  async create(dto: CreateHotelDto): Promise<HotelResponse> {
    const hotel: HotelModel = {
      id: crypto.randomUUID(),
      destinationId: dto.destinationId,
      partnerId: dto.partnerId,
      name: dto.name,
      description: dto.description || {},
      amenities: dto.amenities || {},
      address: dto.address || {},
      stars: dto.stars,
      category: dto.category,
      email: dto.email,
      phone: dto.phone,
      website: dto.website,
      latitude: dto.latitude,
      longitude: dto.longitude,
      pricePerNight: dto.pricePerNight,
      currency: dto.currency || 'USD',
      coverImageUrl: dto.coverImageUrl,
      images: dto.images || [],
      rating: 0,
      reviewCount: 0,
      isActive: true,
      isVerified: false,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.logger.log(`Hotel created: ${hotel.id}`);
    return localizeHotel(hotel, 'en');
  }

  async findAll(filter: HotelFilterDto): Promise<{ hotels: HotelResponse[]; total: number }> {
    return { hotels: [], total: 0 };
  }

  async findById(id: string, language: string = 'en'): Promise<HotelResponse> {
    throw new NotFoundException(`Hotel ${id} not found`);
  }

  async search(query: string, language: string = 'en', limit: number = 10): Promise<HotelResponse[]> {
    return [];
  }

  async update(id: string, dto: UpdateHotelDto, language: string = 'en'): Promise<HotelResponse> {
    throw new NotFoundException(`Hotel ${id} not found`);
  }

  async delete(id: string): Promise<void> {
    this.logger.log(`Hotel deleted: ${id}`);
  }

  async checkAvailability(hotelId: string, checkIn: Date, checkOut: Date): Promise<any> {
    const nights = Math.ceil((checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24));
    return { available: true, pricePerNight: 0, totalPrice: 0, nights, currency: 'USD' };
  }

  async getAiRecommendations(destinationId: string, language: string, travelStyle?: string, budget?: string, groupType?: string): Promise<any> {
    return this.aiService.recommendHotels({ destination: destinationId, hotels: [], language, travelStyle, budget, groupType });
  }

  async updateRating(hotelId: string): Promise<void> {
    this.logger.log(`Hotel ${hotelId} rating updated`);
  }

  async getStats(): Promise<any> {
    return { total: 0, verified: 0, byCategory: {}, avgRating: 0 };
  }
}