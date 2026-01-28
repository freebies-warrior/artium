"use client";

import * as React from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X, Gem } from "lucide-react";
import { Button } from "./ui/Button";

type BidButtonProps = {
  nftName?: string;
  currentPriceSGD?: number;
  minBidSGD?: number;
  triggerText?: string;
};

function fmtSGD(n: number) {
  // Keep simple like the example
  return n.toFixed(2).replace(/\.00$/, "");
}

export default function BidButton({
  nftName = "The Orbitians",
  currentPriceSGD = 1.63,
  minBidSGD = 2.63,
  triggerText = "Place Bid",
}: BidButtonProps) {
  const [bid, setBid] = React.useState<string>("");

  const minBidStr = fmtSGD(minBidSGD);
  const currentPriceStr = fmtSGD(currentPriceSGD);

  const bidValue = bid === "" ? NaN : Number(bid);
  const canSubmit = Number.isFinite(bidValue) && bidValue >= minBidSGD;

  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <Button className="inline-flex items-center justify-center font-semibold rounded-xl transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background disabled:opacity-50 disabled:pointer-events-none cursor-pointer bg-purple-600 text-white hover:bg-purple-700 active:scale-[0.99] h-12 px-8 text-base w-full">
          {triggerText}
        </Button>
      </Dialog.Trigger>

      <Dialog.Portal>
        {/* Overlay */}
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />

        {/* Content */}
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 grid gap-4
                     border border-border bg-neutral-800 p-6 shadow-lg
                     data-[state=open]:animate-in data-[state=closed]:animate-out
                     data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
                     data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95
                     data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]
                     data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]
                     sm:rounded-lg sm:max-w-md"
        >
          {/* Header */}
          <div className="bg-neutral-850 flex flex-col space-y-1.5 text-center sm:text-left">
            <Dialog.Title className="tracking-tight text-xl font-bold">
              Place a Bid
            </Dialog.Title>
            <Dialog.Description className="text-sm text-muted-foreground">
              You are about to place a bid on{" "}
              <span className="text-primary font-medium">{nftName}</span>
            </Dialog.Description>
          </div>

          {/* Body */}
          <div className="space-y-6 py-4">
            {/* Price box */}
            <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
              <div>
                <p className="text-sm text-muted-foreground">Current Price</p>
                <p className="text-lg font-semibold flex items-center gap-2">
                  ${currentPriceStr}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Minimum Bid</p>
                <p className="text-lg font-semibold text-primary">
                  ${minBidStr}
                </p>
              </div>
            </div>

            {/* Bid input */}
            <div className="space-y-3">
              <label className="text-sm font-medium">Your Bid</label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  min={minBidSGD}
                  placeholder="Enter bid amount"
                  value={bid}
                  onChange={(e) => setBid(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-base
                             placeholder:text-muted-foreground ring-offset-background
                             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
                             md:text-sm pr-16"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground font-medium">
                  SGD
                </span>
              </div>
            </div>

            {/* Set minimum */}
            <Button
              fullWidth
              onClick={() => setBid(String(minBidSGD))}
            >
              Set Minimum Bid ({minBidStr} SGD)
            </Button>

            {/* Submit */}
            <Button fullWidth>
              Submit Bid
            </Button>
          </div>

          {/* Close */}
          <Dialog.Close asChild>
            <button
              type="button"
              className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity
                         hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2
                         disabled:pointer-events-none"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
