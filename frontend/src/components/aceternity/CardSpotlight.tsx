import React, { forwardRef } from 'react'
import { GlareHover, GlareHoverProps } from '../reactbits/GlareHover'

export interface CardSpotlightProps extends GlareHoverProps {
  radius?: number
  color?: string
}

/**
 * Aceternity UI Card Spotlight Component
 * Unified with the standardized GlareHover engine for consistent Aurora Indigo highlights.
 */
export const CardSpotlight = forwardRef<HTMLDivElement, CardSpotlightProps>(
  ({ radius = 280, color = 'rgba(100, 87, 232, 0.12)', glareSize, glareColor, ...props }, ref) => {
    return (
      <GlareHover
        ref={ref}
        glareSize={glareSize || radius}
        glareColor={glareColor || color}
        {...props}
      />
    )
  }
)

CardSpotlight.displayName = 'CardSpotlight'

export default CardSpotlight
