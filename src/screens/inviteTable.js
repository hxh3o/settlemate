import { useEffect, useMemo, useState } from 'react';
import { MaterialReactTable, useMaterialReactTable } from 'material-react-table';
import { useNavigate } from 'react-router-dom';
import Modal from '@mui/material/Modal';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { toast } from 'react-toastify';
import { API, authHeaders } from '../api';

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

const InviteTable = () => {
	const [data, setData] = useState([]);
	const [isError, setIsError] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [isRefetching, setIsRefetching] = useState(false);
	const [rowCount, setRowCount] = useState(0);
	const [currTrip, setCurrTrip] = useState({
		name: '',
		owner: { name: '', email: '' },
	});
	const [inviteOpen, setInviteModal] = useState(false);

	const [columnFilters, setColumnFilters] = useState([]);
	const [globalFilter, setGlobalFilter] = useState('');
	const [sorting, setSorting] = useState([]);
	const [pagination, setPagination] = useState({
		pageIndex: 0,
		pageSize: 10,
	});

	useEffect(() => {
		const fetchData = async () => {
			const chkAuth = localStorage.getItem('authToken');
			if (!chkAuth) return;
			if (!data.length) {
				setIsLoading(true);
			} else {
				setIsRefetching(true);
			}

            try {
                const response = await fetch(`${API}/getInvites`, {
                    method: 'GET',
                    headers: authHeaders(),
                });
				const json = await response.json();
				console.log(json);
				if (json.success) {
					setData(json.data);
					setRowCount(json.data.length);
					console.log(json.data);
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
		fetchData();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const columns = useMemo(
		() => [
			{
				accessorKey: 'name',
				header: 'Trip Name',
			},
			{
				accessorKey: 'owner.name',
				header: 'Trip Owner name',
			},
			{
				accessorKey: 'owner.email',
				header: 'Trip Owner Email',
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
		getRowId: row => row,
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
				setCurrTrip(row.id);
				console.log(row.id);
				setInviteModal(true);
			},
			sx: {
				cursor: 'pointer',
			},
		}),
	});

    const acceptInvite = async () => {
        const response = await fetch(`${API}/acceptInvite`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                invite_id: currTrip._id,
            }),
        });
		const json = await response.json();
		if (json.success) {
			if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
			navigate('/trip', { state: { tripid: currTrip.tripid } });
			setInviteModal(false);
		} else {
			localStorage.removeItem('authToken');
			localStorage.setItem('forcedLogOut', true);
			navigate('/');
		}
	};
    const rejectInvite = async () => {
        const response = await fetch(`${API}/declineInvite`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                invite_id: currTrip._id,
            }),
        });
		const json = await response.json();
		if (json.success) {
			if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
			setInviteModal(false);
			setData(prevData => prevData.filter(trip => trip._id !== currTrip._id));
			toast.success('Invite Removed!');
		} else {
			localStorage.removeItem('authToken');
			localStorage.setItem('forcedLogOut', true);
			navigate('/');
		}
	};

	return (
		<>
			<Modal
				open={inviteOpen}
				onClose={() => {
					setInviteModal(false);
				}}
				aria-labelledby='modal-modal-titleinvite'
				aria-describedby='modal-modal-descriptioninvite'
			>
				<Box sx={style}>
					<Typography variant='h5'>{currTrip.name}</Typography>
					<Typography>{currTrip.owner.name}</Typography>
					<Typography>{currTrip.owner.email}</Typography>
					<Button id='modal-modal-descriptioninvite' sx={{ mt: 2 }} variant='contained' onClick={acceptInvite}>
						Accept Invite
					</Button>
					<Button id='modal-modal-descriptioninvite' sx={{ mt: 2 }} variant='contained' onClick={rejectInvite}>
						Reject Invite
					</Button>
				</Box>
			</Modal>
			<MaterialReactTable table={table} />
		</>
	);
};

export default InviteTable;
