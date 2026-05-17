"use client"

import dynamic from "next/dynamic"

const FarmMap = dynamic(() => import("./farm-map"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-muted animate-pulse rounded-md flex items-center justify-center border">Loading Map...</div>
})

export function MapWrapper({ fields = [] }: { fields?: any[] }) {
  return <FarmMap fields={fields} />
}
