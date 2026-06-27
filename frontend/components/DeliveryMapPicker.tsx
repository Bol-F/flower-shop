"use client";

import { useEffect, useRef, useState } from "react";
import type {
  LatLngExpression,
  LeafletMouseEvent,
  Map as LeafletMap,
  Marker as LeafletMarker,
} from "leaflet";

export interface DeliveryMapValue {
  address: string;
  lat: number | null;
  lng: number | null;
}

interface DeliveryMapPickerProps {
  value: DeliveryMapValue;
  onChange: (value: DeliveryMapValue) => void;
}

type LeafletModule = typeof import("leaflet");

const TASHKENT_CENTER: LatLngExpression = [41.311081, 69.240562];

function hasDeliveryPoint(value: DeliveryMapValue): value is DeliveryMapValue & {
  lat: number;
  lng: number;
} {
  return value.lat !== null && value.lng !== null;
}

export default function DeliveryMapPicker({
  value,
  onChange,
}: DeliveryMapPickerProps) {
  const mapElementRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markerRef = useRef<LeafletMarker | null>(null);
  const leafletRef = useRef<LeafletModule | null>(null);
  const initialValueRef = useRef(value);
  const queryRef = useRef(value.address);
  const onChangeRef = useRef(onChange);
  const placeMarkerRef = useRef<(lat: number, lng: number) => void>(() => {});
  const [query, setQuery] = useState(value.address);
  const [searching, setSearching] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    queryRef.current = query;
  }, [query]);

  useEffect(() => {
    let cancelled = false;

    async function initMap() {
      if (!mapElementRef.current || mapRef.current) return;

      const L = await import("leaflet");
      if (cancelled || !mapElementRef.current) return;

      leafletRef.current = L;
      const initialValue = initialValueRef.current;
      const initialCenter = hasDeliveryPoint(initialValue)
        ? ([initialValue.lat, initialValue.lng] as LatLngExpression)
        : TASHKENT_CENTER;
      const map = L.map(mapElementRef.current, {
        scrollWheelZoom: false,
      }).setView(initialCenter, hasDeliveryPoint(initialValue) ? 15 : 12);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(map);

      const markerIcon = L.divIcon({
        className: "",
        html:
          '<span style="display:block;width:22px;height:22px;border-radius:9999px;background:#ec1682;border:4px solid white;box-shadow:0 8px 20px rgba(48,43,45,.32)"></span>',
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      });

      function placeMarker(lat: number, lng: number) {
        if (markerRef.current) {
          markerRef.current.setLatLng([lat, lng]);
        } else {
          markerRef.current = L.marker([lat, lng], { icon: markerIcon }).addTo(map);
        }
      }

      placeMarkerRef.current = placeMarker;
      if (hasDeliveryPoint(initialValue)) {
        placeMarker(initialValue.lat, initialValue.lng);
      }

      map.on("click", (event: LeafletMouseEvent) => {
        const lat = Number(event.latlng.lat.toFixed(6));
        const lng = Number(event.latlng.lng.toFixed(6));
        const address = queryRef.current.trim() || "Selected map point";
        placeMarker(lat, lng);
        setQuery(address);
        setNotice("Delivery point selected.");
        onChangeRef.current({ address, lat, lng });
      });

      mapRef.current = map;
      window.setTimeout(() => map.invalidateSize(), 0);
    }

    void initMap();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
      markerRef.current = null;
      leafletRef.current = null;
    };
  }, []);

  async function searchAddress() {
    const term = query.trim();
    if (!term) {
      setNotice("Type an address or click the map.");
      return;
    }

    try {
      setSearching(true);
      setNotice("");
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(
          term,
        )}`,
      );
      if (!response.ok) throw new Error("Address search failed.");

      const results = (await response.json()) as Array<{
        lat: string;
        lon: string;
        display_name: string;
      }>;
      const result = results[0];

      if (!result) {
        onChange({ ...value, address: term });
        setNotice("Address saved manually. Click the map for the exact point.");
        return;
      }

      const lat = Number(Number.parseFloat(result.lat).toFixed(6));
      const lng = Number(Number.parseFloat(result.lon).toFixed(6));
      const nextValue = {
        address: result.display_name,
        lat,
        lng,
      };
      setQuery(result.display_name);
      placeMarkerRef.current(lat, lng);
      mapRef.current?.setView([lat, lng], 15);
      onChange(nextValue);
      setNotice("Address found on OpenStreetMap.");
    } catch (error) {
      onChange({ ...value, address: term });
      setNotice(
        error instanceof Error
          ? `${error.message} Address saved manually.`
          : "Address saved manually.",
      );
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="grid gap-2">
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(event) => {
            const address = event.target.value;
            setQuery(address);
            onChange({ ...value, address });
          }}
          placeholder="Search or type delivery address"
          className="min-w-0 flex-1 rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
        />
        <button
          type="button"
          onClick={searchAddress}
          disabled={searching}
          className="shrink-0 rounded-2xl bg-ink px-4 py-2.5 text-sm font-extrabold text-white transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70"
        >
          {searching ? "..." : "Find"}
        </button>
      </div>
      <div
        ref={mapElementRef}
        className="h-56 overflow-hidden rounded-2xl border border-line bg-skywash"
      />
      <div className="min-h-5 text-xs font-semibold text-stone">
        {hasDeliveryPoint(value)
          ? `Selected: ${value.lat.toFixed(6)}, ${value.lng.toFixed(6)}`
          : notice || "Click the map to place the delivery marker."}
      </div>
      {notice && hasDeliveryPoint(value) && (
        <p className="text-xs font-semibold text-leaf">{notice}</p>
      )}
    </div>
  );
}
