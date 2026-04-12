import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import Prisma from '@prisma/client';
const { PrismaClient } = Prisma;
import {
  HotelModel,
  HotelResponse,
  CreateHotelDto,
  UpdateHotelDto,
  HotelFilterDto,
  localizeHotel,
} from './hotel.model';
import { AiService } from '../ai/ai.service';

// ─────────────────────────────────────────
// Prisma Client singleton
// ─────────────────────────────────────────

const prisma = new PrismaClient();

// ─────────────────────────────────────────
// Service
// ─────────────────────────────────────────

@Injectable()
export class HotelService {
  private readonly logger = new Logger(HotelService.name);

  constructor(private readonly aiService: AiService) {}

  // ─────────────────────────────────────
  // Créer un hôtel
  // ─────────────────────────────────────

  async create(dto: CreateHotelDto): Promise<HotelResponse> {
    try {
      const hotel = await prisma.hotel.create({
        data: {
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
        },
      });

      this.logger.log(`Hotel created: ${hotel.id}`);
      return localizeHotel(hotel as any, 'en');

    } catch (error) {
      this.logger.error(`create hotel failed: ${error.message}`);
      throw error;
    }
  }

  // ─────────────────────────────────────
  // Lister les hôtels avec filtres
  // ─────────────────────────────────────

  async findAll(
    filter: HotelFilterDto,
  ): Promise<{ hotels: HotelResponse[]; total: number }> {
    try {
      const language = filter.language || 'en';
      const page = filter.page || 1;
      const limit = filter.limit || 20;
      const skip = (page - 1) * limit;

      // Construire les filtres Prisma
      const where: any = { isActive: true };

      if (filter.destinationId) {
        where.destinationId = filter.destinationId;
      }
      if (filter.stars) {
        where.stars = filter.stars;
      }
      if (filter.category) {
        where.category = filter.category;
      }
      if (filter.minPrice || filter.maxPrice) {
        where.pricePerNight = {};
        if (filter.minPrice) where.pricePerNight.gte = filter.minPrice;
        if (filter.maxPrice) where.pricePerNight.lte = filter.maxPrice;
      }

      // Tri
      const orderBy: any = {};
      if (filter.sortBy === 'price') {
        orderBy.pricePerNight = filter.sortOrder || 'asc';
      } else if (filter.sortBy === 'stars') {
        orderBy.stars = filter.sortOrder || 'desc';
      } else {
        orderBy.rating = 'desc';
      }

      // Requête DB
      const [hotels, total] = await Promise.all([
        prisma.hotel.findMany({
          where,
          orderBy,
          skip,
          take: limit,
        }),
        prisma.hotel.count({ where }),
      ]);

      return {
        hotels: hotels.map((h) => localizeHotel(h as any, language)),
        total,
      };

    } catch (error) {
      this.logger.error(`findAll hotels failed: ${error.message}`);
      throw error;
    }
  }

  // ─────────────────────────────────────
  // Trouver un hôtel par ID
  // ─────────────────────────────────────

  async findById(
    id: string,
    language: string = 'en',
  ): Promise<HotelResponse> {
    try {
      const hotel = await prisma.hotel.findUnique({
        where: { id },
      });

      if (!hotel) {
        throw new NotFoundException(`Hotel ${id} not found`);
      }

      return localizeHotel(hotel as any, language);

    } catch (error) {
      this.logger.error(`findById hotel failed: ${error.message}`);
      throw error;
    }
  }

  // ─────────────────────────────────────
  // Recherche par texte
  // ─────────────────────────────────────

  async search(
    query: string,
    language: string = 'en',
    limit: number = 10,
  ): Promise<HotelResponse[]> {
    try {
      const hotels = await prisma.hotel.findMany({
        where: {
          isActive: true,
          OR: [
            {
              name: {
                path: [language],
                string_contains: query,
              },
            },
            {
              name: {
                path: ['en'],
                string_contains: query,
              },
            },
          ],
        },
        take: limit,
        orderBy: { rating: 'desc' },
      });

      return hotels.map((h) => localizeHotel(h as any, language));

    } catch (error) {
      this.logger.error(`search hotels failed: ${error.message}`);
      throw error;
    }
  }

  // ─────────────────────────────────────
  // Mettre à jour un hôtel
  // ─────────────────────────────────────

  async update(
    id: string,
    dto: UpdateHotelDto,
    language: string = 'en',
  ): Promise<HotelResponse> {
    try {
      const hotel = await prisma.hotel.update({
        where: { id },
        data: {
          ...(dto.name && { name: dto.name }),
          ...(dto.description && { description: dto.description }),
          ...(dto.amenities && { amenities: dto.amenities }),
          ...(dto.address && { address: dto.address }),
          ...(dto.stars && { stars: dto.stars }),
          ...(dto.category && { category: dto.category }),
          ...(dto.pricePerNight && { pricePerNight: dto.pricePerNight }),
          ...(dto.coverImageUrl && { coverImageUrl: dto.coverImageUrl }),
          ...(dto.images && { images: dto.images }),
        },
      });

      this.logger.log(`Hotel updated: ${id}`);
      return localizeHotel(hotel as any, language);

    } catch (error) {
      this.logger.error(`update hotel failed: ${error.message}`);
      throw error;
    }
  }

  // ─────────────────────────────────────
  // Supprimer un hôtel (soft delete)
  // ─────────────────────────────────────

  async delete(id: string): Promise<void> {
    try {
      await prisma.hotel.update({
        where: { id },
        data: { isActive: false },
      });
      this.logger.log(`Hotel soft deleted: ${id}`);
    } catch (error) {
      this.logger.error(`delete hotel failed: ${error.message}`);
      throw error;
    }
  }

  // ─────────────────────────────────────
  // Vérifier disponibilité
  // ─────────────────────────────────────

  async checkAvailability(
    hotelId: string,
    checkIn: Date,
    checkOut: Date,
  ): Promise<{
    available: boolean;
    pricePerNight: number;
    totalPrice: number;
    nights: number;
    currency: string;
  }> {
    try {
      const hotel = await prisma.hotel.findUnique({
        where: { id: hotelId },
      });

      if (!hotel) throw new NotFoundException(`Hotel ${hotelId} not found`);

      const nights = Math.ceil(
        (checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24),
      );

      // Vérifier les réservations existantes
      const existingBookings = await prisma.booking.count({
        where: {
          hotelId,
          status: { in: ['pending', 'confirmed'] },
          OR: [
            {
              checkIn: { lte: checkOut },
              checkOut: { gte: checkIn },
            },
          ],
        },
      });

      const pricePerNight = Number(hotel.pricePerNight);

      return {
        available: existingBookings === 0,
        pricePerNight,
        totalPrice: this.round(pricePerNight * nights),
        nights,
        currency: hotel.currency,
      };

    } catch (error) {
      this.logger.error(`checkAvailability failed: ${error.message}`);
      throw error;
    }
  }

  // ─────────────────────────────────────
  // Recommandations IA
  // ─────────────────────────────────────

  async getAiRecommendations(
    destinationId: string,
    language: string,
    travelStyle?: string,
    budget?: string,
    groupType?: string,
  ): Promise<{ recommendations: string; language: string }> {
    try {
      const { hotels } = await this.findAll({ destinationId, language });

      const hotelsData = hotels.map((h) => ({
        name: h.name,
        stars: h.stars,
        price: h.pricePerNight,
        rating: h.rating,
        category: h.category,
      }));

      return this.aiService.recommendHotels({
        destination: destinationId,
        hotels: hotelsData,
        language,
        travelStyle,
        budget,
        groupType,
      });

    } catch (error) {
      this.logger.error(`AI recommendations failed: ${error.message}`);
      throw error;
    }
  }

  // ─────────────────────────────────────
  // Mettre à jour le rating
  // ─────────────────────────────────────

  async updateRating(hotelId: string): Promise<void> {
    try {
      const reviews = await prisma.review.findMany({
        where: { hotelId, isPublished: true },
        select: { rating: true },
      });

      if (reviews.length === 0) return;

      const avgRating = reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length;

      await prisma.hotel.update({
        where: { id: hotelId },
        data: {
          rating: this.round(avgRating),
          reviewCount: reviews.length,
        },
      });

      this.logger.log(`Hotel ${hotelId} rating updated: ${avgRating}`);
    } catch (error) {
      this.logger.error(`updateRating failed: ${error.message}`);
    }
  }

  // ─────────────────────────────────────
  // Stats (admin)
  // ─────────────────────────────────────

  async getStats(): Promise<{
    total: number;
    verified: number;
    byCategory: Record<string, number>;
    avgRating: number;
  }> {
    try {
      const [total, verified, hotels] = await Promise.all([
        prisma.hotel.count({ where: { isActive: true } }),
        prisma.hotel.count({ where: { isActive: true, isVerified: true } }),
        prisma.hotel.findMany({
          where: { isActive: true },
          select: { category: true, rating: true },
        }),
      ]);

      const byCategory: Record<string, number> = {};
      let totalRating = 0;

      hotels.forEach((h) => {
        const cat = h.category || 'hotel';
        byCategory[cat] = (byCategory[cat] || 0) + 1;
        totalRating += Number(h.rating);
      });

      return {
        total,
        verified,
        byCategory,
        avgRating: total > 0 ? this.round(totalRating / total) : 0,
      };

    } catch (error) {
      this.logger.error(`getStats failed: ${error.message}`);
      throw error;
    }
  }

  // ─────────────────────────────────────
  // Helper
  // ─────────────────────────────────────

  private round(n: number): number {
    return Math.round(n * 100) / 100;
  }
}