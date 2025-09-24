import { useEffect, useMemo, useState } from 'react';
import { MaterialReactTable, useMaterialReactTable } from 'material-react-table';
import { API, authHeaders } from '../api';
import { useNavigate } from 'react-router-dom';
import Modal from '@mui/material/Modal';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import QRCode from 'qrcode';

const style = {
	position: 'absolute',
	top: '50%',
	left: '50%',
	transform: 'translate(-50%, -50%)',
	width: 'auto',
	maxWidth: '50%',
	height: 'auto',
	maxHeight: '50%',
	bgcolor: 'background.paper',
	border: '2px solid #000',
	boxShadow: 24,
	p: 4,
	display: 'flex',
	justifyContent: 'center',
	alignItems: 'center',
	flexDirection: 'column',
};

const TransactionTable = ({ tripid }) => {
	const [data, setData] = useState([]);
	const [isError, setIsError] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [isRefetching, setIsRefetching] = useState(false);
	const [rowCount, setRowCount] = useState(0);
	const [modalOpen, setModal] = useState(false);
	const [curr, setCurr] = useState({
		amt: 0,
		from: { name: '', email: '' },
		to: { name: '', email: '', upi: '' },
	});
	const [qrCode, setQrCode] = useState(null);
	const [columnFilters, setColumnFilters] = useState([]);
	const [globalFilter, setGlobalFilter] = useState('');
	const [sorting, setSorting] = useState([]);
	const [pagination, setPagination] = useState({
		pageIndex: 0,
		pageSize: 10,
	});

	useEffect(() => {
		const fetchData = async () => {
			if (!data.length) {
				setIsLoading(true);
			} else {
				setIsRefetching(true);
			}

            try {
                const response = await fetch(`${API}/getTripTransfers`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({
                        tripid: tripid,
                    }),
                });
                const json = await response.json();
                if (json.success) {
                    if (json.notintrip) navigate('/');
                    const items = Array.isArray(json.data) ? json.data : [];
                    // Normalize both backend shapes: {from,to,amt} and {from_user,to_user,amount}
                    const normalized = items.map(item => ({
                        amt: item.amt !== undefined ? item.amt : item.amount,
                        from: item.from || item.from_user || { name: '', email: '' },
                        to: item.to || item.to_user || { name: '', email: '', upi: '' },
                    }));
                    setData(normalized);
                    setRowCount(normalized.length);
					// console.log(json.data);
					if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
				} else {
					localStorage.removeItem('authToken');
					localStorage.setItem('forcedLogOut', true);
					navigate('/profile');
				}
			} catch (error) {
				setIsError(true);
				console.error('Error fetching userData :', error);
				return;
			}
			setIsError(false);
			setIsLoading(false);
			setIsRefetching(false);
		};
		if (tripid) fetchData();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [tripid]);

	const columns = useMemo(
		() => [
			{
				accessorKey: 'from.name',
				header: 'Debtor Name (from)',
			},
			{
				accessorKey: 'from.email',
				header: 'Debtor Email (from)',
			},
			{
				accessorKey: 'amt',
				header: 'Amount',
			},
			{
				accessorKey: 'to.name',
				header: 'Creditor (to)',
			},
			{
				accessorKey: 'to.email',
				header: 'Creditor Email (to)',
			},
			{
				accessorKey: 'to.upi',
				header: 'Creditor UPI (to)',
			},
		],
		[]
	);
	const navigate = useNavigate();
    const table = useMaterialReactTable({
		columns,
		data,
		enableRowSelection: false,
		enableColumnFilters: false,
        getRowId: row => {
            const fromEmail = row?.from?.email || row?.from?.name || 'from';
            const toEmail = row?.to?.email || row?.to?.name || 'to';
            const amt = row?.amt ?? '0';
            return `${fromEmail}-${toEmail}-${amt}`;
        },
		initialState: { showColumnFilters: false },
		manualFiltering: false,
		manualPagination: false,
		manualSorting: false,
		muiToolbarAlertBannerProps: isError
			? {
					color: 'error',
					children: 'Error loading data',
			  }
			: undefined,
		onColumnFiltersChange: setColumnFilters,
		onGlobalFilterChange: setGlobalFilter,
		onPaginationChange: setPagination,
		onSortingChange: setSorting,
		rowCount,
		state: {
			columnFilters,
			globalFilter,
			isLoading,
			pagination,
			showAlertBanner: isError,
			showProgressBars: isRefetching,
			sorting,
		},
		muiTableBodyRowProps: ({ row }) => ({
			onClick: () => {
				setCurr(row.id);
				let upi = `upi://pay?pa=${row.id.to.upi}&tn=SettleMate&am=${row.id.amt}&cu=INR`;
				QRCode.toDataURL(upi, {
					type: 'image/png',
					margin: 1,
					width: 300,
				}).then(res => setQrCode(res));
				setModal(true);
			},
			sx: {
				cursor: 'pointer',
			},
		}),
	});

	return (
		<>
			<Modal
				open={modalOpen}
				onClose={() => {
					setModal(false);
				}}
				aria-labelledby='modal-modal-titleinvite'
				aria-describedby='modal-modal-descriptioninvite'
			>
				<Box sx={style}>
					<div style={{ display: 'flex', gap: '10px' }}>
						<Typography
							style={{
								display: 'flex',
								flexDirection: 'column',
								alignItems: 'center',
							}}
						>
							<div>{curr.from.name}</div>
							<div>{curr.from.email}</div>
						</Typography>
						<Typography
							style={{
								display: 'flex',
								flexDirection: 'column',
								alignItems: 'center',
							}}
						>
							<div> will pay {curr.amt} INR to </div>
						</Typography>
						<Typography
							style={{
								display: 'flex',
								flexDirection: 'column',
								alignItems: 'center',
							}}
						>
							<div>{curr.to.name}</div>
							<div>{curr.to.email}</div>
							<div>{curr.to.upi}</div>
						</Typography>
					</div>
					<img src={qrCode} alt='QR Code' />
				</Box>
			</Modal>
			<MaterialReactTable table={table} />
		</>
	);
};

export default TransactionTable;
