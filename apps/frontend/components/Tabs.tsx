'use client';

import { motion } from "framer-motion";
import "../global.css";

interface TabsProps {
  activeTab: "arts" | "sellers";
  onTabChange: (tab: "arts" | "sellers") => void;
}

export default function Tabs({
  activeTab,
  onTabChange,
}: TabsProps) {
  return (
    <div className="border-b border-border">
      <div className="container mx-auto px-4">
        <div className="flex">
          <button
            onClick={() => onTabChange("arts")}
            className={`tab-button ${activeTab === "arts" ? "active" : ""}`}
          >
            Arts
            {activeTab === "arts" && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-muted-foreground"
              />
            )}
          </button>

          <button
            onClick={() => onTabChange("sellers")}
            className={`tab-button ${activeTab === "sellers" ? "active" : ""}`}
          >
            Sellers
            {activeTab === "sellers" && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-muted-foreground"
              />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
