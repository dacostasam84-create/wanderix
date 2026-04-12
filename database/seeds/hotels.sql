-- ═══════════════════════════════════════════════════════
--  WANDERIX — Seeds Hôtels
-- ═══════════════════════════════════════════════════════

INSERT INTO hotels (
  id, name, description, amenities, address,
  stars, category, email, phone,
  latitude, longitude,
  price_per_night, currency,
  cover_image_url, images,
  rating, review_count,
  is_active, is_verified
) VALUES

-- 1. Marrakech
(
  gen_random_uuid(),
  '{"en":"La Mamounia","fr":"La Mamounia","ar":"لا مامونيا","es":"La Mamounia"}',
  '{"en":"Legendary palace hotel in Marrakech with stunning gardens","fr":"Hôtel palace légendaire à Marrakech avec des jardins magnifiques","ar":"فندق قصر أسطوري في مراكش مع حدائق رائعة","es":"Legendario hotel palacio en Marrakech con jardines impresionantes"}',
  '{"en":"Pool, Spa, Restaurant, Bar, Garden, WiFi","fr":"Piscine, Spa, Restaurant, Bar, Jardin, WiFi","ar":"مسبح، سبا، مطعم، حديقة، واي فاي","es":"Piscina, Spa, Restaurante, Bar, Jardín, WiFi"}',
  '{"en":"Avenue Bab Jdid, Marrakech 40040, Morocco","fr":"Avenue Bab Jdid, Marrakech 40040, Maroc","ar":"شارع باب الجديد، مراكش 40040، المغرب","es":"Avenida Bab Jdid, Marrakech 40040, Marruecos"}',
  5, 'hotel',
  'reservations@mamounia.com', '+212524388600',
  31.6225, -7.9898,
  800.00, 'USD',
  'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800',
  ARRAY['https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800'],
  4.9, 1250,
  true, true
),

-- 2. Paris
(
  gen_random_uuid(),
  '{"en":"Le Meurice","fr":"Le Meurice","ar":"لو موريس","es":"Le Meurice"}',
  '{"en":"Palace hotel facing the Tuileries Garden in Paris","fr":"Hôtel palace face au Jardin des Tuileries à Paris","ar":"فندق قصر مقابل حديقة التويلري في باريس","es":"Hotel palacio frente al Jardín de las Tullerías en París"}',
  '{"en":"Spa, Restaurant, Bar, Concierge, WiFi, Room Service","fr":"Spa, Restaurant, Bar, Conciergerie, WiFi, Room Service","ar":"سبا، مطعم، بار، خدمة الغرف، واي فاي","es":"Spa, Restaurante, Bar, Conserjería, WiFi, Servicio de habitaciones"}',
  '{"en":"228 Rue de Rivoli, 75001 Paris, France","fr":"228 Rue de Rivoli, 75001 Paris, France","ar":"228 شارع دو ريفولي، باريس 75001، فرنسا","es":"228 Rue de Rivoli, 75001 París, Francia"}',
  5, 'hotel',
  'reservations@lemeurice.com', '+33144581010',
  48.8638, 2.3292,
  1200.00, 'USD',
  'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800',
  ARRAY['https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=800'],
  4.8, 890,
  true, true
),

-- 3. Dubai
(
  gen_random_uuid(),
  '{"en":"Burj Al Arab","fr":"Burj Al Arab","ar":"برج العرب","es":"Burj Al Arab"}',
  '{"en":"Iconic 7-star hotel on its own island in Dubai","fr":"Iconique hôtel 7 étoiles sur sa propre île à Dubaï","ar":"الفندق الأيقوني ذو 7 نجوم على جزيرته الخاصة في دبي","es":"Icónico hotel de 7 estrellas en su propia isla en Dubái"}',
  '{"en":"Private Beach, Helipad, Pool, Spa, Multiple Restaurants, Butler Service","fr":"Plage privée, Héliport, Piscine, Spa, Restaurants, Service Majordome","ar":"شاطئ خاص، مهبط طائرات، مسبح، سبا، مطاعم متعددة","es":"Playa privada, Helipuerto, Piscina, Spa, Restaurantes, Mayordomo"}',
  '{"en":"Jumeirah Beach Road, Dubai, UAE","fr":"Jumeirah Beach Road, Dubaï, EAU","ar":"طريق جميرا بيتش، دبي، الإمارات","es":"Jumeirah Beach Road, Dubái, EAU"}',
  5, 'hotel',
  'btreservations@jumeirah.com', '+97143017777',
  25.1412, 55.1853,
  2500.00, 'USD',
  'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800',
  ARRAY['https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800'],
  4.7, 2100,
  true, true
),

-- 4. Barcelona
(
  gen_random_uuid(),
  '{"en":"Hotel Arts Barcelona","fr":"Hotel Arts Barcelone","ar":"فندق آرتس برشلونة","es":"Hotel Arts Barcelona"}',
  '{"en":"Luxury skyscraper hotel on the Barcelona seafront","fr":"Hôtel de luxe en gratte-ciel sur le front de mer de Barcelone","ar":"فندق فاخر ناطح سحاب على واجهة بحر برشلونة","es":"Lujoso hotel rascacielos en el frente marítimo de Barcelona"}',
  '{"en":"Beach Access, Pool, Spa, Restaurant, Bar, WiFi","fr":"Accès plage, Piscine, Spa, Restaurant, Bar, WiFi","ar":"الوصول إلى الشاطئ، مسبح، سبا، مطعم، بار","es":"Acceso playa, Piscina, Spa, Restaurante, Bar, WiFi"}',
  '{"en":"Carrer de la Marina 19-21, 08005 Barcelona, Spain","fr":"Carrer de la Marina 19-21, 08005 Barcelone, Espagne","ar":"شارع