import {
  AirVent, Axe, BadgeCheck, Bath, BatteryCharging, Blinds, BrickWall, Brush, Building2, Cable, Cake,
  CalendarCheck, CarFront, ClipboardCheck, Clock, CloudRain, Coffee, Construction, CookingPot, Croissant,
  DoorOpen, Drill, Droplets, Fan, Fence, FileCheck, Flame, Flower2, Gauge, Hammer, Handshake, HardHat,
  Heater, House, Layers, Leaf, Lightbulb, Mail, MapPin, MessageCircle, Paintbrush, PaintRoller, Phone,
  Pickaxe, Plug, PlugZap, Receipt, Ruler, Sandwich, Scissors, ShieldCheck, ShowerHead, Shovel, Siren,
  Snowflake, SolarPanel, Sprout, Store, Thermometer, ThumbsUp, Timer, TreeDeciduous, Truck, Umbrella,
  Users, UtensilsCrossed, Warehouse, Wheat, Wrench, Zap,
  type LucideIcon,
} from "lucide-react";
import type { ComponentType } from "react";
import {
  EvChargerIcon, FuseBoardIcon, LightSwitchIcon, PendantIcon, RewireIcon, SmokeAlarmIcon, SocketIcon, TesterIcon,
} from "@/components/ElectricIcons";

type IconCmp = LucideIcon | ComponentType<{ className?: string; strokeWidth?: number; "aria-hidden"?: boolean | "true" }>;

/**
 * The only icon set sections use: lucide-react, one stroke weight. Content
 * refers to icons by these names ("icon": "plug-zap" in content.json), so
 * the AI copywriter and the operator pick from a known list. Unknown names
 * fall back to a check mark rather than crashing the page.
 */
export const ICONS: Record<string, IconCmp> = {
  "air-vent": AirVent, axe: Axe, badge: BadgeCheck, bath: Bath, "ev-charger": BatteryCharging,
  blinds: Blinds, "brick-wall": BrickWall, brush: Brush, building: Building2, cable: Cable, cake: Cake,
  calendar: CalendarCheck, car: CarFront, clipboard: ClipboardCheck, clock: Clock, rain: CloudRain,
  coffee: Coffee, construction: Construction, "cooking-pot": CookingPot, croissant: Croissant,
  door: DoorOpen, drill: Drill, droplets: Droplets, fan: Fan, fence: Fence, certificate: FileCheck,
  flame: Flame, flower: Flower2, gauge: Gauge, hammer: Hammer, handshake: Handshake, "hard-hat": HardHat,
  heater: Heater, house: House, layers: Layers, leaf: Leaf, lightbulb: Lightbulb, mail: Mail,
  pin: MapPin, message: MessageCircle, paintbrush: Paintbrush, "paint-roller": PaintRoller, phone: Phone,
  pickaxe: Pickaxe, plug: Plug, "plug-zap": PlugZap, receipt: Receipt, ruler: Ruler, sandwich: Sandwich,
  scissors: Scissors, shield: ShieldCheck, shower: ShowerHead, shovel: Shovel, siren: Siren,
  snowflake: Snowflake, solar: SolarPanel, sprout: Sprout, store: Store, thermometer: Thermometer,
  "thumbs-up": ThumbsUp, timer: Timer, tree: TreeDeciduous, truck: Truck, umbrella: Umbrella,
  users: Users, utensils: UtensilsCrossed, warehouse: Warehouse, wheat: Wheat, wrench: Wrench, zap: Zap,
  // Electrician set (ElectricIcons.tsx), drawn to match lucide.
  socket: SocketIcon, "fuse-board": FuseBoardIcon, "ev-wall": EvChargerIcon, pendant: PendantIcon,
  "smoke-alarm": SmokeAlarmIcon, "light-switch": LightSwitchIcon, tester: TesterIcon, rewire: RewireIcon,
};

export function Icon({ name, className, strokeWidth = 1.6 }: { name?: string; className?: string; strokeWidth?: number }) {
  const Cmp = (name && ICONS[name]) || BadgeCheck;
  return <Cmp aria-hidden="true" className={className} strokeWidth={strokeWidth} />;
}

// Lucide has no brand marks, so WhatsApp is shown as a message bubble plus its name.
export {
  Phone as PhoneIcon,
  Mail as MailIcon,
  MapPin as PinIcon,
  MessageCircle as WhatsAppIcon,
  Clock as ClockIcon,
  Star as StarIcon,
  ArrowRight as ArrowIcon,
  ArrowUpRight as ExternalIcon,
} from "lucide-react";
