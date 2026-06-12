import TrustBar from "@/components/TrustBar";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import CategoryNav from "@/components/CategoryNav";
import Catalog from "@/components/Catalog";
import GiftFinder from "@/components/GiftFinder";
import BouquetBuilder from "@/components/BouquetBuilder";
import Reviews from "@/components/Reviews";
import WhyChooseUs from "@/components/WhyChooseUs";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <TrustBar />
      <Header />
      <main>
        <Hero />
        <CategoryNav />
        <Catalog />
        <GiftFinder />
        <BouquetBuilder />
        <Reviews />
        <WhyChooseUs />
      </main>
      <Footer />
    </>
  );
}
