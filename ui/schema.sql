-- ============================================================================
-- CAMPUS MARKET — COMPLETE POSTGRESQL / SUPABASE DATABASE SCHEMA
-- Specialized P2P Marketplace for University Students
-- ============================================================================

-- Enable required UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. USERS & PROFILES TABLE (Strict .edu Auth & Identity Assurance)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL CHECK (email LIKE '%.edu' OR email LIKE '%.ac.uk'),
    university VARCHAR(150) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    avatar_url TEXT,
    graduation_year INT NOT NULL,
    major VARCHAR(100),
    bio TEXT,
    verified_student BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    rating NUMERIC(3, 2) DEFAULT 5.00 CHECK (rating >= 1.00 AND rating <= 5.00),
    review_count INT DEFAULT 0,
    enrolled_courses TEXT[], -- e.g. ARRAY['CS 101', 'MATH 202', 'PHYS 41']
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 2. CAMPUS SAFE ZONES TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS campus_safe_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university VARCHAR(150) NOT NULL,
    name VARCHAR(150) NOT NULL,
    building VARCHAR(150),
    description TEXT,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    security_type VARCHAR(50) CHECK (security_type IN ('24/7 Police Station', 'Monitored Student Union', 'Library Security Desk', 'Lit Quad Spot')),
    operating_hours VARCHAR(100) DEFAULT '24/7',
    is_active BOOLEAN DEFAULT TRUE
);

-- ----------------------------------------------------------------------------
-- 3. LISTINGS TABLE (Buy, Sell, Rent + High-Value Vehicle Specifications)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('textbooks', 'calculators', 'lab_gear', 'electronics', 'furniture', 'vehicles', 'dorm_essentials', 'apparel')),
    transaction_mode VARCHAR(20) NOT NULL CHECK (transaction_mode IN ('buy', 'sell', 'rent')),
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    rental_daily_rate DECIMAL(10, 2) CHECK (rental_daily_rate IS NULL OR rental_daily_rate >= 0),
    rental_weekly_rate DECIMAL(10, 2) CHECK (rental_weekly_rate IS NULL OR rental_weekly_rate >= 0),
    security_deposit DECIMAL(10, 2) DEFAULT 0.00 CHECK (security_deposit >= 0),
    condition VARCHAR(50) NOT NULL CHECK (condition IN ('Brand New', 'Like New', 'Good', 'Fair')),
    images TEXT[] NOT NULL,
    
    -- Vehicle / High-Value Dedicated Specs
    is_vehicle BOOLEAN DEFAULT FALSE,
    vehicle_specs JSONB DEFAULT '{}'::jsonb, 
    -- Format: { "vin": "1HGCR2F83HA000000", "mileage": 45000, "registration_status": "Current", "title_status": "Clean Title", "fuel_type": "Gasoline" }
    
    -- Standardized Inspection & Condition Checklist (Mandatory before publishing vehicles/electronics)
    condition_checklist JSONB DEFAULT '{}'::jsonb,
    -- Format: { "inspected_by_seller": true, "brakes_tires_ok": true, "no_engine_lights": true, "battery_health_pct": 95, "inspected_at": "2026-08-04" }

    preferred_safe_zone_id UUID REFERENCES campus_safe_zones(id),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'pending_escrow', 'rented', 'sold', 'archived')),
    is_dorm_sweep BOOLEAN DEFAULT FALSE,
    view_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 4. COURSE TAGS TABLE (Academic Integration & Course Code Matching)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS course_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    course_code VARCHAR(30) NOT NULL, -- e.g., 'CS 101', 'MATH 202', 'CHEM 31A'
    course_name VARCHAR(150),
    professor_name VARCHAR(120),
    term VARCHAR(30) -- e.g., 'Fall 2026'
);

-- ----------------------------------------------------------------------------
-- 5. RENTAL RESERVATIONS & DIGITAL CONTRACTS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rentals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES listings(id),
    renter_id UUID NOT NULL REFERENCES profiles(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_rental_fee DECIMAL(10, 2) NOT NULL,
    security_deposit_hold DECIMAL(10, 2) NOT NULL,
    stripe_preauth_hold_id VARCHAR(255),
    digital_contract_accepted BOOLEAN DEFAULT FALSE,
    renter_signature VARCHAR(150),
    contract_signed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('pending', 'active', 'returned', 'overdue', 'disputed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 6. TRANSACTIONS & ESCROW PAYMENTS (Hold Payments Until Physical Handoff)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES listings(id),
    buyer_id UUID NOT NULL REFERENCES profiles(id),
    seller_id UUID NOT NULL REFERENCES profiles(id),
    amount DECIMAL(10, 2) NOT NULL,
    stripe_payment_intent_id VARCHAR(255),
    escrow_status VARCHAR(30) DEFAULT 'held' CHECK (escrow_status IN ('held', 'buyer_confirmed', 'seller_confirmed', 'released', 'refunded', 'disputed')),
    buyer_confirmed_handoff BOOLEAN DEFAULT FALSE,
    seller_confirmed_handoff BOOLEAN DEFAULT FALSE,
    handoff_verification_pin VARCHAR(6) NOT NULL,
    meetup_safe_zone_id UUID REFERENCES campus_safe_zones(id),
    meetup_scheduled_at TIMESTAMP WITH TIME ZONE,
    released_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 7. "IN SEARCH OF" (ISO) PUBLIC REQUEST BOARD
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS iso_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    course_code VARCHAR(30),
    max_budget DECIMAL(10, 2) NOT NULL,
    needed_by DATE,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'fulfilled', 'closed')),
    fulfillment_listing_id UUID REFERENCES listings(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 8. IN-APP MESSAGES & OFFER NEGOTIATIONS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID REFERENCES listings(id),
    sender_id UUID NOT NULL REFERENCES profiles(id),
    receiver_id UUID NOT NULL REFERENCES profiles(id),
    content TEXT NOT NULL,
    offer_amount DECIMAL(10, 2),
    offer_status VARCHAR(20) CHECK (offer_status IN ('pending', 'accepted', 'declined', 'expired')),
    suggested_safe_zone_id UUID REFERENCES campus_safe_zones(id),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE rentals ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE iso_requests ENABLE ROW LEVEL SECURITY;

-- Public can view verified active profiles and listings
CREATE POLICY "Public Profiles Read" ON profiles FOR SELECT USING (true);
CREATE POLICY "Public Listings Read" ON listings FOR SELECT USING (status = 'active' OR seller_id = auth.uid());
CREATE POLICY "Public Safe Zones Read" ON campus_safe_zones FOR SELECT USING (true);

-- Authenticated Users can create & edit their own records
CREATE POLICY "Users Update Own Profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users Insert Listings" ON listings FOR INSERT WITH CHECK (auth.uid() = seller_id);
CREATE POLICY "Users Update Own Listings" ON listings FOR UPDATE USING (auth.uid() = seller_id);

-- Messages & Transactions privacy
CREATE POLICY "Users Read Own Messages" ON messages FOR SELECT USING (auth.uid() = sender_id OR auth.uid() = receiver_id);
CREATE POLICY "Users Send Messages" ON messages FOR INSERT WITH CHECK (auth.uid() = sender_id);
CREATE POLICY "Users Read Own Transactions" ON transactions FOR SELECT USING (auth.uid() = buyer_id OR auth.uid() = seller_id);
