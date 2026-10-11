import * as React from 'react'
import { motion, AnimatePresence, HTMLMotionProps } from 'framer-motion'
import { PanelLeft, PanelLeftClose } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip'

interface SidebarContextValue {
  open: boolean
  setOpen: (open: boolean) => void
  toggleSidebar: () => void
  isMobile: boolean
}

const SidebarContext = React.createContext<SidebarContextValue | null>(null)

export function useSidebar() {
  const context = React.useContext(SidebarContext)
  if (!context) {
    throw new Error('useSidebar must be used within a SidebarProvider.')
  }
  return context
}

export const SidebarProvider = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<'div'> & {
    defaultOpen?: boolean
    open?: boolean
    onOpenChange?: (open: boolean) => void
  }
>(({ defaultOpen = true, open: openProp, onOpenChange, className, children, ...props }, ref) => {
  const [_open, _setOpen] = React.useState(defaultOpen)
  const open = openProp !== undefined ? openProp : _open

  const setOpen = React.useCallback(
    (value: boolean) => {
      if (onOpenChange) {
        onOpenChange(value)
      } else {
        _setOpen(value)
      }
    },
    [onOpenChange]
  )

  const toggleSidebar = React.useCallback(() => {
    setOpen(!open)
  }, [open, setOpen])

  return (
    <SidebarContext.Provider
      value={{
        open,
        setOpen,
        toggleSidebar,
        isMobile: false,
      }}
    >
      <TooltipProvider delayDuration={100}>
        <div ref={ref} className={cn('flex min-h-screen w-full', className)} {...props}>
          {children}
        </div>
      </TooltipProvider>
    </SidebarContext.Provider>
  )
})
SidebarProvider.displayName = 'SidebarProvider'

export const Sidebar = React.forwardRef<
  HTMLElement,
  HTMLMotionProps<'aside'>
>(({ className, children, ...props }, ref) => {
  const { open } = useSidebar()

  return (
    <motion.aside
      ref={ref}
      initial={false}
      animate={{ width: open ? 256 : 72 }}
      transition={{ duration: 0.24, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        'relative z-30 flex h-screen flex-col border-r border-[#212348] bg-[#13152E] text-slate-100 select-none overflow-hidden shrink-0 font-sans',
        open ? 'w-64' : 'w-[72px]',
        className
      )}
      {...props}
    >
      {children}
    </motion.aside>
  )
})
Sidebar.displayName = 'Sidebar'

export const SidebarHeader = React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex h-14 shrink-0 items-center border-b border-[#212348] px-4', className)}
      {...props}
    />
  )
)
SidebarHeader.displayName = 'SidebarHeader'

export const SidebarContent = React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex-1 overflow-y-auto overflow-x-hidden py-3 px-2 space-y-5', className)}
      {...props}
    />
  )
)
SidebarContent.displayName = 'SidebarContent'

export const SidebarGroup = React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col space-y-1', className)} {...props} />
  )
)
SidebarGroup.displayName = 'SidebarGroup'

export const SidebarGroupLabel = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<'div'> & { asChild?: boolean }
>(({ className, children, ...props }, ref) => {
  const { open } = useSidebar()
  if (!open) {
    return <div className="h-2" />
  }
  return (
    <div
      ref={ref}
      className={cn(
        'px-3 py-1 text-[11px] font-semibold tracking-wider text-slate-400 uppercase font-sans truncate',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
})
SidebarGroupLabel.displayName = 'SidebarGroupLabel'

export const SidebarGroupContent = React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn('space-y-0.5', className)} {...props} />
)
SidebarGroupContent.displayName = 'SidebarGroupContent'

export const SidebarMenu = React.forwardRef<HTMLUListElement, React.ComponentProps<'ul'>>(
  ({ className, ...props }, ref) => (
    <ul ref={ref} className={cn('flex flex-col space-y-0.5 list-none m-0 p-0', className)} {...props} />
  )
)
SidebarMenu.displayName = 'SidebarMenu'

export const SidebarMenuItem = React.forwardRef<HTMLLIElement, React.ComponentProps<'li'>>(
  ({ className, ...props }, ref) => <li ref={ref} className={cn('relative', className)} {...props} />
)
SidebarMenuItem.displayName = 'SidebarMenuItem'

export const SidebarMenuButton = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<'button'> & {
    isActive?: boolean
    tooltip?: string
  }
>(({ className, isActive, tooltip, children, ...props }, ref) => {
  const { open } = useSidebar()

  const button = (
    <button
      ref={ref}
      className={cn(
        'group relative flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150 outline-none cursor-pointer text-left',
        isActive
          ? 'bg-gradient-to-r from-[#3A326F] to-[#29264F] text-white font-semibold shadow-sm'
          : 'text-slate-300 hover:bg-[#212348] hover:text-white',
        !open && 'justify-center px-0 py-2.5',
        className
      )}
      {...props}
    >
      {isActive && (
        <motion.span
          layoutId="sidebarActiveIndicator"
          className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-md bg-[#8B5CF6]"
          transition={{ type: 'spring', stiffness: 450, damping: 35 }}
        />
      )}
      {children}
    </button>
  )

  if (!open && tooltip) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{button}</TooltipTrigger>
        <TooltipContent side="right" className="bg-[#13152E] text-white border-[#212348] shadow-xl">
          {tooltip}
        </TooltipContent>
      </Tooltip>
    )
  }

  return button
})
SidebarMenuButton.displayName = 'SidebarMenuButton'

export const SidebarFooter = React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col shrink-0 border-t border-[#212348] p-3 space-y-2 bg-[#0E1024]', className)}
      {...props}
    />
  )
)
SidebarFooter.displayName = 'SidebarFooter'

export const SidebarTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<'button'>
>(({ className, ...props }, ref) => {
  const { open, toggleSidebar } = useSidebar()
  return (
    <button
      ref={ref}
      id="sidebar-toggle-btn"
      onClick={toggleSidebar}
      className={cn(
        'p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-[#212348] transition-colors cursor-pointer',
        className
      )}
      title={open ? 'Collapse sidebar' : 'Expand sidebar'}
      {...props}
    >
      {open ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
    </button>
  )
})
SidebarTrigger.displayName = 'SidebarTrigger'
