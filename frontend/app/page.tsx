import Hero from "@/components/Hero";
import CategoryRail from "@/components/CategoryRail";
import Catalog from "@/components/Catalog";
import PerksStrip from "@/components/PerksStrip";
import ReviewsMarquee from "@/components/ReviewsMarquee";

export default function Home() {
  return (
    <main>
      <Hero />
      <CategoryRail />
      <Catalog />
      <PerksStrip />
      <ReviewsMarquee />
    </main>
  );
}
