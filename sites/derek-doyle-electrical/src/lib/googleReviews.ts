export type GoogleReview = {
  author: string;
  rating: number;
  text: string;
  relativeTime: string;
};

export type ReviewsResult = {
  reviews: GoogleReview[];
  mapsUrl: string;
  isLive: boolean;
};

const BUSINESS_QUERY = "{{BUSINESS_NAME}} {{TOWN}}";
const FALLBACK_MAPS_URL =
  "https://www.google.com/maps/search/?api=1&query=" +
  encodeURIComponent(BUSINESS_QUERY);

const FALLBACK_REVIEWS: GoogleReview[] = [
  {
    author: "Niamh O'Brien",
    rating: 5,
    text: "{{OWNER_FIRST_NAME}} rewired our whole house in Drumcondra last month. Tidy work, fair price and the cert was ready same day. Would absolutely recommend.",
    relativeTime: "{{TOWN}}",
  },
  {
    author: "Seán Farrell",
    rating: 5,
    text: "Called {{OWNER_FIRST_NAME}} at 11pm with a complete power failure. He was with us within the hour and had everything sorted before midnight. Unreal service.",
    relativeTime: "{{TOWN}}",
  },
  {
    author: "Aoife McCarthy",
    rating: 5,
    text: "Had our EV charger and solar panels installed by {{OWNER_FIRST_NAME}}. Sorted the SEAI grant paperwork and the job was done inside a week.",
    relativeTime: "{{TOWN}}",
  },
];

export async function getGoogleReviews(): Promise<ReviewsResult> {
  const apiKey = process.env.GOOGLE_PLACES_API_KEY;

  if (!apiKey) {
    return { reviews: FALLBACK_REVIEWS, mapsUrl: FALLBACK_MAPS_URL, isLive: false };
  }

  try {
    const findUrl =
      "https://maps.googleapis.com/maps/api/place/findplacefromtext/json" +
      `?input=${encodeURIComponent(BUSINESS_QUERY)}` +
      "&inputtype=textquery&fields=place_id" +
      `&key=${apiKey}`;

    const findRes = await fetch(findUrl, { next: { revalidate: 86400 } });
    const findData = await findRes.json();
    const placeId: string | undefined = findData?.candidates?.[0]?.place_id;

    if (!placeId) {
      return { reviews: FALLBACK_REVIEWS, mapsUrl: FALLBACK_MAPS_URL, isLive: false };
    }

    const detailsUrl =
      "https://maps.googleapis.com/maps/api/place/details/json" +
      `?place_id=${placeId}` +
      "&fields=review,url" +
      `&key=${apiKey}`;

    const detailsRes = await fetch(detailsUrl, { next: { revalidate: 86400 } });
    const detailsData = await detailsRes.json();

    const rawReviews: {
      author_name: string;
      rating: number;
      text: string;
      relative_time_description: string;
    }[] = detailsData?.result?.reviews ?? [];

    if (rawReviews.length === 0) {
      return { reviews: FALLBACK_REVIEWS, mapsUrl: FALLBACK_MAPS_URL, isLive: false };
    }

    const reviews: GoogleReview[] = rawReviews.slice(0, 5).map((r) => ({
      author: r.author_name,
      rating: r.rating,
      text: r.text,
      relativeTime: r.relative_time_description,
    }));

    return {
      reviews,
      mapsUrl: detailsData?.result?.url ?? FALLBACK_MAPS_URL,
      isLive: true,
    };
  } catch {
    return { reviews: FALLBACK_REVIEWS, mapsUrl: FALLBACK_MAPS_URL, isLive: false };
  }
}
