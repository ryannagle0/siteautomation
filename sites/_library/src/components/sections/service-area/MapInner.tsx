"use client";

import { Map, MapMarker, MarkerContent } from "@/components/ui/map";

export default function MapInner({ lng, lat, dark }: { lng: number; lat: number; dark: boolean }) {
  return (
    <Map center={[lng, lat]} zoom={10.5} theme={dark ? "dark" : "light"} cooperativeGestures attributionControl={{ compact: true }}>
      <MapMarker longitude={lng} latitude={lat}>
        <MarkerContent>
          <span className="block h-5 w-5 rounded-full border-2 border-white bg-accent shadow-[0_2px_8px_rgb(0_0_0/0.35)]" />
        </MarkerContent>
      </MapMarker>
    </Map>
  );
}
