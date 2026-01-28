import { Paintbrush, Box } from "lucide-react";
import categoryPaintings from "@/assets/category-paintings.jpg";
import categorySculptures from "@/assets/category-sculptures.jpg";

const categories = [
  {
    name: "Paintings",
    icon: Paintbrush,
    image: categoryPaintings,
  },
  {
    name: "Sculptures",
    icon: Box,
    image: categorySculptures,
  },
];

const BrowseCategories = () => {
  return (
    <section className="py-16 md:py-24">
      <div className="container mx-auto px-4">
        <h2 className="font-display text-3xl md:text-4xl font-bold mb-12">
          Browse Categories
        </h2>

        <div className="grid sm:grid-cols-2 gap-6">
          {categories.map((category, index) => (
            <div
              key={index}
              className="group relative rounded-2xl overflow-hidden cursor-pointer"
            >
              <img
                src={category.image}
                alt={category.name}
                className="w-full aspect-[4/3] object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/20 to-transparent" />
              <div className="absolute bottom-6 left-6 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-card/80 backdrop-blur-sm flex items-center justify-center">
                  <category.icon className="w-5 h-5 text-primary" />
                </div>
                <span className="font-display font-semibold text-lg text-foreground">
                  {category.name}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BrowseCategories;
